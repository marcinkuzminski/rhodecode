from celery.decorators import task
from celery.task.sets import subtask
from celeryconfig import PYLONS_CONFIG as config
from datetime import datetime, timedelta
from pylons.i18n.translation import _
from pylons_app.lib.celerylib import run_task
from pylons_app.lib.helpers import person
from pylons_app.lib.smtp_mailer import SmtpMailer
from pylons_app.lib.utils import OrderedDict
from operator import itemgetter
from vcs.backends.hg import MercurialRepository
from time import mktime
import calendar
import traceback
import json

__all__ = ['whoosh_index', 'get_commits_stats',
           'reset_user_password', 'send_email']

def get_session():
    from sqlalchemy import engine_from_config
    from sqlalchemy.orm import sessionmaker, scoped_session
    engine = engine_from_config(dict(config.items('app:main')), 'sqlalchemy.db1.')
    sa = scoped_session(sessionmaker(bind=engine))
    return sa

def get_hg_settings():
    from pylons_app.model.db import HgAppSettings
    try:
        sa = get_session()
        ret = sa.query(HgAppSettings).all()
    finally:
        sa.remove()
        
    if not ret:
        raise Exception('Could not get application settings !')
    settings = {}
    for each in ret:
        settings['hg_app_' + each.app_settings_name] = each.app_settings_value    
    
    return settings

def get_hg_ui_settings():
    from pylons_app.model.db import HgAppUi
    try:
        sa = get_session()
        ret = sa.query(HgAppUi).all()
    finally:
        sa.remove()
        
    if not ret:
        raise Exception('Could not get application ui settings !')
    settings = {}
    for each in ret:
        k = each.ui_key
        v = each.ui_value
        if k == '/':
            k = 'root_path'
        
        if k.find('.') != -1:
            k = k.replace('.', '_')
        
        if each.ui_section == 'hooks':
            v = each.ui_active
        
        settings[each.ui_section + '_' + k] = v  
    
    return settings   

@task
def whoosh_index(repo_location, full_index):
    log = whoosh_index.get_logger()
    from pylons_app.lib.indexers import DaemonLock
    from pylons_app.lib.indexers.daemon import WhooshIndexingDaemon, LockHeld
    try:
        l = DaemonLock()
        WhooshIndexingDaemon(repo_location=repo_location)\
            .run(full_index=full_index)
        l.release()
        return 'Done'
    except LockHeld:
        log.info('LockHeld')
        return 'LockHeld'    

@task
def get_commits_stats(repo):
    log = get_commits_stats.get_logger()
    aggregate = OrderedDict()
    overview_aggregate = OrderedDict()
    repos_path = get_hg_ui_settings()['paths_root_path'].replace('*', '')
    repo = MercurialRepository(repos_path + repo)
    #graph range
    td = datetime.today() + timedelta(days=1) 
    y, m, d = td.year, td.month, td.day
    
    ts_min_y = mktime((y - 1, (td - timedelta(days=calendar.mdays[m])).month,
                        d, 0, 0, 0, 0, 0, 0,))
    ts_min_m = mktime((y, (td - timedelta(days=calendar.mdays[m])).month,
                        d, 0, 0, 0, 0, 0, 0,))
    
    ts_max_y = mktime((y, m, d, 0, 0, 0, 0, 0, 0,))
    skip_date_limit = True
    
    def author_key_cleaner(k):
        k = person(k)
        k = k.replace('"', "") #for js data compatibilty
        return k
            
    for cs in repo[:200]:#added limit 200 until fix #29 is made
        k = '%s-%s-%s' % (cs.date.timetuple()[0], cs.date.timetuple()[1],
                          cs.date.timetuple()[2])
        timetupple = [int(x) for x in k.split('-')]
        timetupple.extend([0 for _ in xrange(6)])
        k = mktime(timetupple)
        if aggregate.has_key(author_key_cleaner(cs.author)):
            if aggregate[author_key_cleaner(cs.author)].has_key(k):
                aggregate[author_key_cleaner(cs.author)][k]["commits"] += 1
                aggregate[author_key_cleaner(cs.author)][k]["added"] += len(cs.added)
                aggregate[author_key_cleaner(cs.author)][k]["changed"] += len(cs.changed)
                aggregate[author_key_cleaner(cs.author)][k]["removed"] += len(cs.removed)
                
            else:
                #aggregate[author_key_cleaner(cs.author)].update(dates_range)
                if k >= ts_min_y and k <= ts_max_y or skip_date_limit:
                    aggregate[author_key_cleaner(cs.author)][k] = {}
                    aggregate[author_key_cleaner(cs.author)][k]["commits"] = 1
                    aggregate[author_key_cleaner(cs.author)][k]["added"] = len(cs.added)
                    aggregate[author_key_cleaner(cs.author)][k]["changed"] = len(cs.changed)
                    aggregate[author_key_cleaner(cs.author)][k]["removed"] = len(cs.removed) 
                                        
        else:
            if k >= ts_min_y and k <= ts_max_y or skip_date_limit:
                aggregate[author_key_cleaner(cs.author)] = OrderedDict()
                #aggregate[author_key_cleaner(cs.author)].update(dates_range)
                aggregate[author_key_cleaner(cs.author)][k] = {}
                aggregate[author_key_cleaner(cs.author)][k]["commits"] = 1
                aggregate[author_key_cleaner(cs.author)][k]["added"] = len(cs.added)
                aggregate[author_key_cleaner(cs.author)][k]["changed"] = len(cs.changed)
                aggregate[author_key_cleaner(cs.author)][k]["removed"] = len(cs.removed)                 
    
        
        if overview_aggregate.has_key(k):
            overview_aggregate[k] += 1
        else:
            overview_aggregate[k] = 1
    
    overview_data = []
    for k, v in overview_aggregate.items():
        overview_data.append([k, v])
    overview_data = sorted(overview_data, key=itemgetter(0))
    data = {}
    for author in aggregate:
        commit_data = sorted([{"time":x,
                               "commits":aggregate[author][x]['commits'],
                               "added":aggregate[author][x]['added'],
                               "changed":aggregate[author][x]['changed'],
                               "removed":aggregate[author][x]['removed'],
                              } for x in aggregate[author]],
                              key=itemgetter('time'))
        
        data[author] = {"label":author,
                      "data":commit_data,
                      "schema":["commits"]
                      }
        
    if not data:
        data[author_key_cleaner(repo.contact)] = {
            "label":author_key_cleaner(repo.contact),
            "data":[0, 1],
            "schema":["commits"],
        }
                
    return (ts_min_m, ts_max_y, json.dumps(data), json.dumps(overview_data))    

@task
def reset_user_password(user_email):
    log = reset_user_password.get_logger()
    from pylons_app.lib import auth
    from pylons_app.model.db import User
    
    try:
        try:
            sa = get_session()
            user = sa.query(User).filter(User.email == user_email).scalar()
            new_passwd = auth.PasswordGenerator().gen_password(8,
                             auth.PasswordGenerator.ALPHABETS_BIG_SMALL)
            user.password = auth.get_crypt_password(new_passwd)
            sa.add(user)
            sa.commit()
            log.info('change password for %s', user_email)
            if new_passwd is None:
                raise Exception('unable to generate new password')
            
        except:
            log.error(traceback.format_exc())
            sa.rollback()
        
        run_task(send_email, user_email,
                 "Your new hg-app password",
                 'Your new hg-app password:%s' % (new_passwd))
        log.info('send new password mail to %s', user_email)
        
        
    except:
        log.error('Failed to update user password')
        log.error(traceback.format_exc())
    return True

@task    
def send_email(recipients, subject, body):
    log = send_email.get_logger()
    email_config = dict(config.items('DEFAULT')) 
    mail_from = email_config.get('app_email_from')
    user = email_config.get('smtp_username')
    passwd = email_config.get('smtp_password')
    mail_server = email_config.get('smtp_server')
    mail_port = email_config.get('smtp_port')
    tls = email_config.get('smtp_use_tls')
    ssl = False
    
    try:
        m = SmtpMailer(mail_from, user, passwd, mail_server,
                       mail_port, ssl, tls)
        m.send(recipients, subject, body)  
    except:
        log.error('Mail sending failed')
        log.error(traceback.format_exc())
        return False
    return True
