# -*- coding: utf-8 -*-
"""
    rhodecode.lib.celerylib.__init__
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    celery libs for RhodeCode

    :created_on: Nov 27, 2010
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

import os
import sys
import socket
import traceback
import logging
from os.path import dirname as dn, join as jn
from pylons import config

from hashlib import md5
from decorator import decorator

from vcs.utils.lazy import LazyProperty

from rhodecode.lib import str2bool, safe_str
from rhodecode.lib.pidlock import DaemonLock, LockHeld
from rhodecode.model import init_model
from rhodecode.model import meta
from rhodecode.model.db import Statistics, Repository, User

from sqlalchemy import engine_from_config

from celery.messaging import establish_connection

log = logging.getLogger(__name__)

try:
    CELERY_ON = str2bool(config['app_conf'].get('use_celery'))
except KeyError:
    CELERY_ON = False


class ResultWrapper(object):
    def __init__(self, task):
        self.task = task

    @LazyProperty
    def result(self):
        return self.task


def run_task(task, *args, **kwargs):
    if CELERY_ON:
        try:
            t = task.apply_async(args=args, kwargs=kwargs)
            log.info('running task %s:%s', t.task_id, task)
            return t

        except socket.error, e:
            if isinstance(e, IOError) and e.errno == 111:
                log.debug('Unable to connect to celeryd. Sync execution')
            else:
                log.error(traceback.format_exc())
        except KeyError, e:
                log.debug('Unable to connect to celeryd. Sync execution')
        except Exception, e:
            log.error(traceback.format_exc())

    log.debug('executing task %s in sync mode', task)
    return ResultWrapper(task(*args, **kwargs))


def __get_lockkey(func, *fargs, **fkwargs):
    params = list(fargs)
    params.extend(['%s-%s' % ar for ar in fkwargs.items()])

    func_name = str(func.__name__) if hasattr(func, '__name__') else str(func)

    lockkey = 'task_%s.lock' % \
        md5(func_name + '-' + '-'.join(map(safe_str, params))).hexdigest()
    return lockkey


def locked_task(func):
    def __wrapper(func, *fargs, **fkwargs):
        lockkey = __get_lockkey(func, *fargs, **fkwargs)
        lockkey_path = config['here']

        log.info('running task with lockkey %s', lockkey)
        try:
            l = DaemonLock(file_=jn(lockkey_path, lockkey))
            ret = func(*fargs, **fkwargs)
            l.release()
            return ret
        except LockHeld:
            log.info('LockHeld')
            return 'Task with key %s already running' % lockkey

    return decorator(__wrapper, func)


def get_session():
    if CELERY_ON:
        engine = engine_from_config(config, 'sqlalchemy.db1.')
        init_model(engine)
    sa = meta.Session
    return sa


def dbsession(func):
    def __wrapper(func, *fargs, **fkwargs):
        try:
            ret = func(*fargs, **fkwargs)
            return ret
        finally:
            if CELERY_ON:
                meta.Session.remove()

    return decorator(__wrapper, func)
