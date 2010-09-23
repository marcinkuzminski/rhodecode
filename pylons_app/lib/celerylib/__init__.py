from pylons_app.lib.pidlock import DaemonLock, LockHeld
from vcs.utils.lazy import LazyProperty
from decorator import decorator
import logging
import os
import sys
import traceback
from hashlib import md5
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
    except Exception, e:
        print e
        if e.errno == 111:
            log.debug('Unnable to connect. Sync execution')
        else:
            log.error(traceback.format_exc())
        #pure sync version
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
            return func(*fargs, **fkwargs)
            l.release()
        except LockHeld:
            log.info('LockHeld')
            return 'Task with key %s already running' % lockkey   

    return decorator(__wrapper, func)      
            

        
        
    
    
    
  
