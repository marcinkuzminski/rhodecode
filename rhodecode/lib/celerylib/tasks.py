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
from os.path import join as jn

from time import mktime
from operator import itemgetter
from string import lower

from pylons import config, url
from pylons.i18n.translation import _

from rhodecode.lib.vcs import get_backend

from rhodecode import CELERY_ON
from rhodecode.lib import LANGUAGES_EXTENSIONS_MAP, safe_str
from rhodecode.lib.celerylib import run_task, locked_task, dbsession, \
    str2bool, __get_lockkey, LockHeld, DaemonLock, get_session
from rhodecode.lib.helpers import person
from rhodecode.lib.rcmail.smtp_mailer import SmtpMailer
from rhodecode.lib.utils import add_cache, action_logger
from rhodecode.lib.compat import json, OrderedDict

from rhodecode.model.db import Statistics, Repository, User


add_cache(config)

__all__ = ['whoosh_index', 'get_commits_stats',
           'reset_user_password', 'send_email']


def get_logger(cls):
    if CELERY_ON:
        try:
            log = cls.get_logger()
        except:
            log = logging.getLogger(__name__)
    else:
        log = logging.getLogger(__name__)

    return log


@task(ignore_result=True)
@locked_task
@dbsession
def whoosh_index(repo_location, full_index):
    from rhodecode.lib.indexers.daemon import WhooshIndexingDaemon
    log = whoosh_index.get_logger(whoosh_index)
    DBS = get_session()

    index_location = config['index_dir']
    WhooshIndexingDaemon(index_location=index_location,
                         repo_location=repo_location, sa=DBS)\
                         .run(full_index=full_index)


@task(ignore_result=True)
@dbsession
def get_commits_stats(repo_name, ts_min_y, ts_max_y):
    log = get_logger(get_commits_stats)
    DBS = get_session()
    lockkey = __get_lockkey('get_commits_stats', repo_name, ts_min_y,
                            ts_max_y)
    lockkey_path = config['here']

    log.info('running task with lockkey %s' % lockkey)

    try:
        lock = l = DaemonLock(file_=jn(lockkey_path, lockkey))

        # for js data compatibility cleans the key for person from '
        akc = lambda k: person(k).replace('"', "")

        co_day_auth_aggr = {}
        commits_by_day_aggregate = {}
        repo = Repository.get_by_repo_name(repo_name)
        if repo is None:
            return True

        repo = repo.scm_instance
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

        dbrepo = DBS.query(Repository)\
            .filter(Repository.repo_name == repo_name).scalar()
        cur_stats = DBS.query(Statistics)\
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

        log.debug('starting parsing %s' % parse_limit)
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

        log.debug('last revison %s' % last_rev)
        leftovers = len(repo.revisions[last_rev:])
        log.debug('revisions to parse %s' % leftovers)

        if last_rev == 0 or leftovers < parse_limit:
            log.debug('getting code trending stats')
            stats.languages = json.dumps(__get_codes_stats(repo_name))

        try:
            stats.repository = dbrepo
            stats.stat_on_revision = last_cs.revision if last_cs else 0
            DBS.add(stats)
            DBS.commit()
        except:
            log.error(traceback.format_exc())
            DBS.rollback()
            lock.release()
            return False

        #final release
        lock.release()

        #execute another task if celery is enabled
        if len(repo.revisions) > 1 and CELERY_ON:
            run_task(get_commits_stats, repo_name, ts_min_y, ts_max_y)
        return True
    except LockHeld:
        log.info('LockHeld')
        return 'Task with key %s already running' % lockkey

@task(ignore_result=True)
@dbsession
def send_password_link(user_email):
    from rhodecode.model.notification import EmailNotificationModel

    log = get_logger(send_password_link)
    DBS = get_session()

    try:
        user = User.get_by_email(user_email)
        if user:
            log.debug('password reset user found %s' % user)
            link = url('reset_password_confirmation', key=user.api_key,
                       qualified=True)
            reg_type = EmailNotificationModel.TYPE_PASSWORD_RESET
            body = EmailNotificationModel().get_email_tmpl(reg_type,
                                                **{'user':user.short_contact,
                                                   'reset_url':link})
            log.debug('sending email')
            run_task(send_email, user_email,
                     _("password reset link"), body)
            log.info('send new password mail to %s' % user_email)
        else:
            log.debug("password reset email %s not found" % user_email)
    except:
        log.error(traceback.format_exc())
        return False

    return True

@task(ignore_result=True)
@dbsession
def reset_user_password(user_email):
    from rhodecode.lib import auth

    log = get_logger(reset_user_password)
    DBS = get_session()

    try:
        try:
            user = User.get_by_email(user_email)
            new_passwd = auth.PasswordGenerator().gen_password(8,
                             auth.PasswordGenerator.ALPHABETS_BIG_SMALL)
            if user:
                user.password = auth.get_crypt_password(new_passwd)
                user.api_key = auth.generate_api_key(user.username)
                DBS.add(user)
                DBS.commit()
                log.info('change password for %s' % user_email)
            if new_passwd is None:
                raise Exception('unable to generate new password')
        except:
            log.error(traceback.format_exc())
            DBS.rollback()

        run_task(send_email, user_email,
                 'Your new password',
                 'Your new RhodeCode password:%s' % (new_passwd))
        log.info('send new password mail to %s' % user_email)

    except:
        log.error('Failed to update user password')
        log.error(traceback.format_exc())

    return True


@task(ignore_result=True)
@dbsession
def send_email(recipients, subject, body, html_body=''):
    """
    Sends an email with defined parameters from the .ini files.

    :param recipients: list of recipients, it this is empty the defined email
        address from field 'email_to' is used instead
    :param subject: subject of the mail
    :param body: body of the mail
    :param html_body: html version of body
    """
    log = get_logger(send_email)
    DBS = get_session()

    email_config = config
    subject = "%s %s" % (email_config.get('email_prefix'), subject)
    if not recipients:
        # if recipients are not defined we send to email_config + all admins
        admins = [u.email for u in User.query()
                  .filter(User.admin == True).all()]
        recipients = [email_config.get('email_to')] + admins

    mail_from = email_config.get('app_email_from', 'RhodeCode')
    user = email_config.get('smtp_username')
    passwd = email_config.get('smtp_password')
    mail_server = email_config.get('smtp_server')
    mail_port = email_config.get('smtp_port')
    tls = str2bool(email_config.get('smtp_use_tls'))
    ssl = str2bool(email_config.get('smtp_use_ssl'))
    debug = str2bool(config.get('debug'))
    smtp_auth = email_config.get('smtp_auth')

    try:
        m = SmtpMailer(mail_from, user, passwd, mail_server, smtp_auth,
                       mail_port, ssl, tls, debug=debug)
        m.send(recipients, subject, body, html_body)
    except:
        log.error('Mail sending failed')
        log.error(traceback.format_exc())
        return False
    return True


@task(ignore_result=True)
@dbsession
def create_repo_fork(form_data, cur_user):
    """
    Creates a fork of repository using interval VCS methods

    :param form_data:
    :param cur_user:
    """
    from rhodecode.model.repo import RepoModel

    log = get_logger(create_repo_fork)
    DBS = get_session()

    base_path = Repository.base_path()

    RepoModel(DBS).create(form_data, cur_user, just_db=True, fork=True)

    alias = form_data['repo_type']
    org_repo_name = form_data['org_path']
    fork_name = form_data['repo_name_full']
    update_after_clone = form_data['update_after_clone']
    source_repo_path = os.path.join(base_path, org_repo_name)
    destination_fork_path = os.path.join(base_path, fork_name)

    log.info('creating fork of %s as %s', source_repo_path,
             destination_fork_path)
    backend = get_backend(alias)
    backend(safe_str(destination_fork_path), create=True,
            src_url=safe_str(source_repo_path),
            update_after_clone=update_after_clone)
    action_logger(cur_user, 'user_forked_repo:%s' % fork_name,
                   org_repo_name, '', DBS)

    action_logger(cur_user, 'user_created_fork:%s' % fork_name,
                   fork_name, '', DBS)
    # finally commit at latest possible stage
    DBS.commit()

def __get_codes_stats(repo_name):
    repo = Repository.get_by_repo_name(repo_name).scm_instance

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
