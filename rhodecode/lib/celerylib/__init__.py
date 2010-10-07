from rhodecode.lib.pidlock import DaemonLock, LockHeld
from vcs.utils.lazy import LazyProperty
from decorator import decorator
import logging
import os
import sys
import traceback
from hashlib import md5
import socket
log = logging.getLogger(__name__)

class ResultWrapper(object):
    def __init__(self, task):
        self.task = task
        
    @LazyProperty
    def result(self):
        return self.task

def run_task(task, *args, **kwargs):
    try:
        t = task.delay(*args, **kwargs)
        log.info('running task %s', t.task_id)
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
            

        
        
    
    
    
  
