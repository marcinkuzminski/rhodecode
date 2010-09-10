from vcs.utils.lazy import LazyProperty
import logging

log = logging.getLogger(__name__)

class ResultWrapper(object):
    def __init__(self, task):
        self.task = task
        
    @LazyProperty
    def result(self):
        return self.task

def run_task(task,async,*args,**kwargs):
    try:
        t = task.delay(*args,**kwargs)
        log.info('running task %s',t.task_id)
        if not async:
            t.wait()
        return t
    except:
        #pure sync version
        return ResultWrapper(task(*args,**kwargs))
    