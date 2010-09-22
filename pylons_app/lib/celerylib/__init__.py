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


class LockTask(object):
    """LockTask decorator"""
    
    def __init__(self, func):
        self.func = func
        
    def __call__(self, func):
        return decorator(self.__wrapper, func)
    
    def __wrapper(self, func, *fargs, **fkwargs):
        params = []
        params.extend(fargs)
        params.extend(fkwargs.values())
        lockkey = 'task_%s' % \
           md5(str(self.func) + '-' + '-'.join(map(str, params))).hexdigest()
        log.info('running task with lockkey %s', lockkey)
        try:
            l = DaemonLock(lockkey)
            return func(*fargs, **fkwargs)
            l.release()
        except LockHeld:
            log.info('LockHeld')
            return 'Task with key %s already running' % lockkey   

            
            

        
        
    
    
    
  
