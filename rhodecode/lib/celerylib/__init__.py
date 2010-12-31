# -*- coding: utf-8 -*-
"""
    package.rhodecode.lib.celerylib.__init__
    ~~~~~~~~~~~~~~

    celery libs for RhodeCode
    
    :created_on: Nov 27, 2010
    :author: marcink
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>    
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your opinion) any later version of the license.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.

import os
import sys
import socket
import traceback
import logging

from hashlib import md5
from decorator import decorator
from vcs.utils.lazy import LazyProperty

from rhodecode.lib.pidlock import DaemonLock, LockHeld

from pylons import  config

log = logging.getLogger(__name__)

def str2bool(v):
    return v.lower() in ["yes", "true", "t", "1"] if v else None

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
            t = task.delay(*args, **kwargs)
            log.info('running task %s:%s', t.task_id, task)
            return t
        except socket.error, e:
            if  e.errno == 111:
                log.debug('Unable to connect to celeryd. Sync execution')
            else:
                log.error(traceback.format_exc())
        except KeyError, e:
                log.debug('Unable to connect to celeryd. Sync execution')
        except Exception, e:
            log.error(traceback.format_exc())

    log.debug('executing task %s in sync mode', task)
    return ResultWrapper(task(*args, **kwargs))


def locked_task(func):
    def __wrapper(func, *fargs, **fkwargs):
        params = list(fargs)
        params.extend(['%s-%s' % ar for ar in fkwargs.items()])

        lockkey = 'task_%s' % \
            md5(str(func.__name__) + '-' + \
                '-'.join(map(str, params))).hexdigest()
        log.info('running task with lockkey %s', lockkey)
        try:
            l = DaemonLock(lockkey)
            ret = func(*fargs, **fkwargs)
            l.release()
            return ret
        except LockHeld:
            log.info('LockHeld')
            return 'Task with key %s already running' % lockkey

    return decorator(__wrapper, func)








