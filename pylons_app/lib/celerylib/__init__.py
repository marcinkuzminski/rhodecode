from vcs.utils.lazy import LazyProperty
import logging
import os
import sys
import traceback

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
        if e.errno == 111:
            log.debug('Unnable to connect. Sync execution')
        else:
            log.error(traceback.format_exc())
        #pure sync version
        return ResultWrapper(task(*args, **kwargs))
    
