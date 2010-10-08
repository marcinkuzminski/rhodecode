from celery.decorators import task

from operator import itemgetter
from pylons.i18n.translation import _
from rhodecode.lib.celerylib import run_task, locked_task
from rhodecode.lib.helpers import person
from rhodecode.lib.smtp_mailer import SmtpMailer
from rhodecode.lib.utils import OrderedDict
from time import mktime
from vcs.backends.hg import MercurialRepository
import json
import traceback

try:
    from celeryconfig import PYLONS_CONFIG as config
    celery_on = True
except ImportError:
    #if celeryconfig is not present let's just load our pylons
    #config instead
    from pylons import config
    celery_on = False


__all__ = ['whoosh_index', 'get_commits_stats',
           'reset_user_password', 'send_email']

def get_session():
    if celery_on:
        from sqlalchemy import engine_from_config
        from sqlalchemy.orm import sessionmaker, scoped_session
        engine = engine_from_config(dict(config.items('app:main')), 'sqlalchemy.db1.')
        sa = scoped_session(sessionmaker(bind=engine))
    else:
        #If we don't use celery reuse our current application Session
        from rhodecode.model.meta import Session
        sa = Session
        
    return sa

def get_hg_settings():
    from rhodecode.model.db import RhodeCodeSettings
    sa = get_session()
    ret = sa.query(RhodeCodeSettings).all()
        
    if not ret:
        raise Exception('Could not get application settings !')
    settings = {}
    for each in ret:
        settings['rhodecode_' + each.app_settings_name] = each.app_settings_value    
    
    return settings

def get_hg_ui_settings():
    from rhodecode.model.db import RhodeCodeUi
    sa = get_session()
    ret = sa.query(RhodeCodeUi).all()
        
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
@locked_task
def whoosh_index(repo_location, full_index):
    log = whoosh_index.get_logger()
    from rhodecode.lib.indexers.daemon import WhooshIndexingDaemon
    WhooshIndexingDaemon(repo_location=repo_location).run(full_index=full_index)

@task
@locked_task
def get_commits_stats(repo_name, ts_min_y, ts_max_y):
    from rhodecode.model.db import Statistics, Repository
    log = get_commits_stats.get_logger()
    author_key_cleaner = lambda k: person(k).replace('"', "") #for js data compatibilty
    
    commits_by_day_author_aggregate = {}
    commits_by_day_aggregate = {}
    repos_path = get_hg_ui_settings()['paths_root_path'].replace('*', '')
    repo = MercurialRepository(repos_path + repo_name)

    skip_date_limit = True
    parse_limit = 350 #limit for single task changeset parsing optimal for
    last_rev = 0
    last_cs = None
    timegetter = itemgetter('time')
    
    sa = get_session()
    
    dbrepo = sa.query(Repository)\
        .filter(Repository.repo_name == repo_name).scalar()
    cur_stats = sa.query(Statistics)\
        .filter(Statistics.repository == dbrepo).scalar()
    if cur_stats:
        last_rev = cur_stats.stat_on_revision
    if not repo.revisions:
        return True
    
    if last_rev == repo.revisions[-1] and len(repo.revisions) > 1:
        #pass silently without any work if we're not on first revision or current
        #state of parsing revision(from db marker) is the last revision
        return True
    
    if cur_stats:
        commits_by_day_aggregate = OrderedDict(
                                       json.loads(
                                        cur_stats.commit_activity_combined))
        commits_by_day_author_aggregate = json.loads(cur_stats.commit_activity)
    
    log.debug('starting parsing %s', parse_limit)
    for cnt, rev in enumerate(repo.revisions[last_rev:]):
        last_cs = cs = repo.get_changeset(rev)
        k = '%s-%s-%s' % (cs.date.timetuple()[0], cs.date.timetuple()[1],
                          cs.date.timetuple()[2])
        timetupple = [int(x) for x in k.split('-')]
        timetupple.extend([0 for _ in xrange(6)])
        k = mktime(timetupple)
        if commits_by_day_author_aggregate.has_key(author_key_cleaner(cs.author)):
            try:
                l = [timegetter(x) for x in commits_by_day_author_aggregate\
                        [author_key_cleaner(cs.author)]['data']]
                time_pos = l.index(k)
            except ValueError:
                time_pos = False
                
            if time_pos >= 0 and time_pos is not False:
                
                datadict = commits_by_day_author_aggregate\
                    [author_key_cleaner(cs.author)]['data'][time_pos]
                
                datadict["commits"] += 1
                datadict["added"] += len(cs.added)
                datadict["changed"] += len(cs.changed)
                datadict["removed"] += len(cs.removed)
                
            else:
                if k >= ts_min_y and k <= ts_max_y or skip_date_limit:
                    
                    datadict = {"time":k,
                                "commits":1,
                                "added":len(cs.added),
                                "changed":len(cs.changed),
                                "removed":len(cs.removed),
                               }
                    commits_by_day_author_aggregate\
                        [author_key_cleaner(cs.author)]['data'].append(datadict)
                                        
        else:
            if k >= ts_min_y and k <= ts_max_y or skip_date_limit:
                commits_by_day_author_aggregate[author_key_cleaner(cs.author)] = {
                                    "label":author_key_cleaner(cs.author),
                                    "data":[{"time":k,
                                             "commits":1,
                                             "added":len(cs.added),
                                             "changed":len(cs.changed),
                                             "removed":len(cs.removed),
                                             }],
                                    "schema":["commits"],
                                    }               
    
        #gather all data by day
        if commits_by_day_aggregate.has_key(k):
            commits_by_day_aggregate[k] += 1
        else:
            commits_by_day_aggregate[k] = 1
        
        if cnt >= parse_limit:
            #don't fetch to much data since we can freeze application
            break

    overview_data = []
    for k, v in commits_by_day_aggregate.items():
        overview_data.append([k, v])
    overview_data = sorted(overview_data, key=itemgetter(0))
        
    if not commits_by_day_author_aggregate:
        commits_by_day_author_aggregate[author_key_cleaner(repo.contact)] = {
            "label":author_key_cleaner(repo.contact),
            "data":[0, 1],
            "schema":["commits"],
        }

    stats = cur_stats if cur_stats else Statistics()
    stats.commit_activity = json.dumps(commits_by_day_author_aggregate)
    stats.commit_activity_combined = json.dumps(overview_data)

    log.debug('last revison %s', last_rev)
    leftovers = len(repo.revisions[last_rev:])
    log.debug('revisions to parse %s', leftovers)
    
    if last_rev == 0 or leftovers < parse_limit:    
        stats.languages = json.dumps(__get_codes_stats(repo_name))
        
    stats.repository = dbrepo
    stats.stat_on_revision = last_cs.revision
    
    try:
        sa.add(stats)
        sa.commit()    
    except:
        log.error(traceback.format_exc())
        sa.rollback()
        return False
    if len(repo.revisions) > 1:
        run_task(get_commits_stats, repo_name, ts_min_y, ts_max_y)
                            
    return True

@task
def reset_user_password(user_email):
    log = reset_user_password.get_logger()
    from rhodecode.lib import auth
    from rhodecode.model.db import User
    
    try:
        try:
            sa = get_session()
            user = sa.query(User).filter(User.email == user_email).scalar()
            new_passwd = auth.PasswordGenerator().gen_password(8,
                             auth.PasswordGenerator.ALPHABETS_BIG_SMALL)
            if user:
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
                 "Your new rhodecode password",
                 'Your new rhodecode password:%s' % (new_passwd))
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

@task
def create_repo_fork(form_data, cur_user):
    import os
    from rhodecode.model.repo_model import RepoModel
    sa = get_session()
    rm = RepoModel(sa)
    
    rm.create(form_data, cur_user, just_db=True, fork=True)
    
    repos_path = get_hg_ui_settings()['paths_root_path'].replace('*', '')
    repo_path = os.path.join(repos_path, form_data['repo_name'])
    repo_fork_path = os.path.join(repos_path, form_data['fork_name'])
    
    MercurialRepository(str(repo_fork_path), True, clone_url=str(repo_path))

    
def __get_codes_stats(repo_name):
    LANGUAGES_EXTENSIONS = ['action', 'adp', 'ashx', 'asmx', 'aspx', 'asx', 'axd', 'c',
                    'cfg', 'cfm', 'cpp', 'cs', 'diff', 'do', 'el', 'erl',
                    'h', 'java', 'js', 'jsp', 'jspx', 'lisp',
                    'lua', 'm', 'mako', 'ml', 'pas', 'patch', 'php', 'php3',
                    'php4', 'phtml', 'pm', 'py', 'rb', 'rst', 's', 'sh',
                    'tpl', 'txt', 'vim', 'wss', 'xhtml', 'xml', 'xsl', 'xslt',
                    'yaws']
    repos_path = get_hg_ui_settings()['paths_root_path'].replace('*', '')
    repo = MercurialRepository(repos_path + repo_name)

    code_stats = {}
    for topnode, dirs, files in repo.walk('/', 'tip'):
        for f in files:
            k = f.mimetype
            if f.extension in LANGUAGES_EXTENSIONS:
                if code_stats.has_key(k):
                    code_stats[k] += 1
                else:
                    code_stats[k] = 1
                    
    return code_stats or {}


            


