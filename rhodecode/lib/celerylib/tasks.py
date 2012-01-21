# -*- coding: utf-8 -*-
"""
    rhodecode.lib.celerylib.tasks
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    RhodeCode task modules, containing all task that suppose to be run
    by celery daemon

    :created_on: Oct 6, 2010
    :author: marcink
    :copyright: (C) 2010-2012 Marcin Kuzminski <marcin@python-works.com>
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from celery.decorators import task

import os
import traceback
import logging
from os.path import dirname as dn, join as jn

from time import mktime
from operator import itemgetter
from string import lower

from pylons import config, url
from pylons.i18n.translation import _

from rhodecode.lib import LANGUAGES_EXTENSIONS_MAP, safe_str
from rhodecode.lib.celerylib import run_task, locked_task, str2bool, \
    __get_lockkey, LockHeld, DaemonLock, get_session, dbsession
from rhodecode.lib.helpers import person
from rhodecode.lib.smtp_mailer import SmtpMailer
from rhodecode.lib.utils import add_cache
from rhodecode.lib.compat import json, OrderedDict

from rhodecode.model.db import RhodeCodeUi, Statistics, Repository, User

from vcs.backends import get_repo
from vcs import get_backend

add_cache(config)

__all__ = ['whoosh_index', 'get_commits_stats',
           'reset_user_password', 'send_email']

CELERY_ON = str2bool(config['app_conf'].get('use_celery'))


def get_repos_path():
    sa = get_session()
    q = sa.query(RhodeCodeUi).filter(RhodeCodeUi.ui_key == '/').one()
    return q.ui_value


@task(ignore_result=True)
@locked_task
@dbsession
def whoosh_index(repo_location, full_index):
    #log = whoosh_index.get_logger()
    from rhodecode.lib.indexers.daemon import WhooshIndexingDaemon
    index_location = config['index_dir']
    WhooshIndexingDaemon(index_location=index_location,
                         repo_location=repo_location, sa=get_session())\
                         .run(full_index=full_index)


@task(ignore_result=True)
@dbsession
def get_commits_stats(repo_name, ts_min_y, ts_max_y):
    try:
        log = get_commits_stats.get_logger()
    except:
        log = logging.getLogger(__name__)

    lockkey = __get_lockkey('get_commits_stats', repo_name, ts_min_y,
                            ts_max_y)
    lockkey_path = config['here']

    log.info('running task with lockkey %s', lockkey)
    try:
        sa = get_session()
        lock = l = DaemonLock(file_=jn(lockkey_path, lockkey))

        # for js data compatibilty cleans the key for person from '
        akc = lambda k: person(k).replace('"', "")

        co_day_auth_aggr = {}
        commits_by_day_aggregate = {}
        repos_path = get_repos_path()
        repo = get_repo(safe_str(os.path.join(repos_path, repo_name)))
        repo_size = repo.count()
        # return if repo have no revisions
        if repo_size < 1:
            lock.release()
            return True

        skip_date_limit = True
        parse_limit = int(config['app_conf'].get('commit_parse_limit'))
        last_rev = None
        last_cs = None
        timegetter = itemgetter('time')

        dbrepo = sa.query(Repository)\
            .filter(Repository.repo_name == repo_name).scalar()
        cur_stats = sa.query(Statistics)\
            .filter(Statistics.repository == dbrepo).scalar()

        if cur_stats is not None:
            last_rev = cur_stats.stat_on_revision

        if last_rev == repo.get_changeset().revision and repo_size > 1:
            # pass silently without any work if we're not on first revision or
            # current state of parsing revision(from db marker) is the
            # last revision
            lock.release()
            return True

        if cur_stats:
            commits_by_day_aggregate = OrderedDict(json.loads(
                                        cur_stats.commit_activity_combined))
            co_day_auth_aggr = json.loads(cur_stats.commit_activity)

        log.debug('starting parsing %s', parse_limit)
        lmktime = mktime

        last_rev = last_rev + 1 if last_rev >= 0 else 0
        log.debug('Getting revisions from %s to %s' % (
             last_rev, last_rev + parse_limit)
        )
        for cs in repo[last_rev:last_rev + parse_limit]:
            last_cs = cs  # remember last parsed changeset
            k = lmktime([cs.date.timetuple()[0], cs.date.timetuple()[1],
                          cs.date.timetuple()[2], 0, 0, 0, 0, 0, 0])

            if akc(cs.author) in co_day_auth_aggr:
                try:
                    l = [timegetter(x) for x in
                         co_day_auth_aggr[akc(cs.author)]['data']]
                    time_pos = l.index(k)
                except ValueError:
                    time_pos = False

                if time_pos >= 0 and time_pos is not False:

                    datadict = \
                        co_day_auth_aggr[akc(cs.author)]['data'][time_pos]

                    datadict["commits"] += 1
                    datadict["added"] += len(cs.added)
                    datadict["changed"] += len(cs.changed)
                    datadict["removed"] += len(cs.removed)

                else:
                    if k >= ts_min_y and k <= ts_max_y or skip_date_limit:

                        datadict = {"time": k,
                                    "commits": 1,
                                    "added": len(cs.added),
                                    "changed": len(cs.changed),
                                    "removed": len(cs.removed),
                                   }
                        co_day_auth_aggr[akc(cs.author)]['data']\
                            .append(datadict)

            else:
                if k >= ts_min_y and k <= ts_max_y or skip_date_limit:
                    co_day_auth_aggr[akc(cs.author)] = {
                                        "label": akc(cs.author),
                                        "data": [{"time":k,
                                                 "commits":1,
                                                 "added":len(cs.added),
                                                 "changed":len(cs.changed),
                                                 "removed":len(cs.removed),
                                                 }],
                                        "schema": ["commits"],
                                        }

            #gather all data by day
            if k in commits_by_day_aggregate:
                commits_by_day_aggregate[k] += 1
            else:
                commits_by_day_aggregate[k] = 1

        overview_data = sorted(commits_by_day_aggregate.items(),
                               key=itemgetter(0))

        if not co_day_auth_aggr:
            co_day_auth_aggr[akc(repo.contact)] = {
                "label": akc(repo.contact),
                "data": [0, 1],
                "schema": ["commits"],
            }

        stats = cur_stats if cur_stats else Statistics()
        stats.commit_activity = json.dumps(co_day_auth_aggr)
        stats.commit_activity_combined = json.dumps(overview_data)

        log.debug('last revison %s', last_rev)
        leftovers = len(repo.revisions[last_rev:])
        log.debug('revisions to parse %s', leftovers)

        if last_rev == 0 or leftovers < parse_limit:
            log.debug('getting code trending stats')
            stats.languages = json.dumps(__get_codes_stats(repo_name))

        try:
            stats.repository = dbrepo
            stats.stat_on_revision = last_cs.revision if last_cs else 0
            sa.add(stats)
            sa.commit()
        except:
            log.error(traceback.format_exc())
            sa.rollback()
            lock.release()
            return False

        # final release
        lock.release()

        # execute another task if celery is enabled
        if len(repo.revisions) > 1 and CELERY_ON:
            run_task(get_commits_stats, repo_name, ts_min_y, ts_max_y)
        return True
    except LockHeld:
        log.info('LockHeld')
        return 'Task with key %s already running' % lockkey

@task(ignore_result=True)
@dbsession
def send_password_link(user_email):
    try:
        log = reset_user_password.get_logger()
    except:
        log = logging.getLogger(__name__)

    from rhodecode.lib import auth

    try:
        sa = get_session()
        user = sa.query(User).filter(User.email == user_email).scalar()

        if user:
            link = url('reset_password_confirmation', key=user.api_key,
                       qualified=True)
            tmpl = """
Hello %s

We received a request to create a new password for your account.

You can generate it by clicking following URL:

%s

If you didn't request new password please ignore this email.
            """
            run_task(send_email, user_email,
                     "RhodeCode password reset link",
                     tmpl % (user.short_contact, link))
            log.info('send new password mail to %s', user_email)

    except:
        log.error('Failed to update user password')
        log.error(traceback.format_exc())
        return False

    return True

@task(ignore_result=True)
@dbsession
def reset_user_password(user_email):
    try:
        log = reset_user_password.get_logger()
    except:
        log = logging.getLogger(__name__)

    from rhodecode.lib import auth

    try:
        try:
            sa = get_session()
            user = sa.query(User).filter(User.email == user_email).scalar()
            new_passwd = auth.PasswordGenerator().gen_password(8,
                             auth.PasswordGenerator.ALPHABETS_BIG_SMALL)
            if user:
                user.password = auth.get_crypt_password(new_passwd)
                user.api_key = auth.generate_api_key(user.username)
                sa.add(user)
                sa.commit()
                log.info('change password for %s', user_email)
            if new_passwd is None:
                raise Exception('unable to generate new password')

        except:
            log.error(traceback.format_exc())
            sa.rollback()

        run_task(send_email, user_email,
                 "Your new RhodeCode password",
                 'Your new RhodeCode password:%s' % (new_passwd))
        log.info('send new password mail to %s', user_email)

    except:
        log.error('Failed to update user password')
        log.error(traceback.format_exc())

    return True


@task(ignore_result=True)
@dbsession
def send_email(recipients, subject, body):
    """
    Sends an email with defined parameters from the .ini files.

    :param recipients: list of recipients, it this is empty the defined email
        address from field 'email_to' is used instead
    :param subject: subject of the mail
    :param body: body of the mail
    """
    try:
        log = send_email.get_logger()
    except:
        log = logging.getLogger(__name__)
    
    sa = get_session()
    email_config = config

    if not recipients:
        # if recipients are not defined we send to email_config + all admins
        admins = [
            u.email for u in sa.query(User).filter(User.admin==True).all()
        ]
        recipients = [email_config.get('email_to')] + admins

    mail_from = email_config.get('app_email_from')
    user = email_config.get('smtp_username')
    passwd = email_config.get('smtp_password')
    mail_server = email_config.get('smtp_server')
    mail_port = email_config.get('smtp_port')
    tls = str2bool(email_config.get('smtp_use_tls'))
    ssl = str2bool(email_config.get('smtp_use_ssl'))
    debug = str2bool(config.get('debug'))
    smtp_auth = email_config.get('smtp_auth')

    try:
        m = SmtpMailer(mail_from, user, passwd, mail_server,smtp_auth,
                       mail_port, ssl, tls, debug=debug)
        m.send(recipients, subject, body)
    except:
        log.error('Mail sending failed')
        log.error(traceback.format_exc())
        return False
    return True


@task(ignore_result=True)
@dbsession
def create_repo_fork(form_data, cur_user):
    from rhodecode.model.repo import RepoModel

    try:
        log = create_repo_fork.get_logger()
    except:
        log = logging.getLogger(__name__)

    repo_model = RepoModel(get_session())
    repo_model.create(form_data, cur_user, just_db=True, fork=True)
    repo_name = form_data['repo_name']
    repos_path = get_repos_path()
    repo_path = os.path.join(repos_path, repo_name)
    repo_fork_path = os.path.join(repos_path, form_data['fork_name'])
    alias = form_data['repo_type']

    log.info('creating repo fork %s as %s', repo_name, repo_path)
    backend = get_backend(alias)
    backend(str(repo_fork_path), create=True, src_url=str(repo_path))


def __get_codes_stats(repo_name):
    repos_path = get_repos_path()
    repo = get_repo(safe_str(os.path.join(repos_path, repo_name)))
    tip = repo.get_changeset()
    code_stats = {}

    def aggregate(cs):
        for f in cs[2]:
            ext = lower(f.extension)
            if ext in LANGUAGES_EXTENSIONS_MAP.keys() and not f.is_binary:
                if ext in code_stats:
                    code_stats[ext] += 1
                else:
                    code_stats[ext] = 1

    map(aggregate, tip.walk('/'))

    return code_stats or {}
