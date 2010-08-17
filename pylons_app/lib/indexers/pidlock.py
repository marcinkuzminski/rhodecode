import os, time
import sys
from warnings import warn

class LockHeld(Exception):pass


class DaemonLock(object):
    '''daemon locking
    USAGE:
    try:
        l = lock()
        main()
        l.release()
    except LockHeld:
        sys.exit(1)
    '''

    def __init__(self, file=None, callbackfn=None,
                 desc='daemon lock', debug=False):

        self.pidfile = file if file else os.path.join(os.path.dirname(__file__),
                                                      'running.lock')
        self.callbackfn = callbackfn
        self.desc = desc
        self.debug = debug
        self.held = False
        #run the lock automatically !
        self.lock()

    def __del__(self):
        if self.held:

#            warn("use lock.release instead of del lock",
#                    category = DeprecationWarning,
#                    stacklevel = 2)

            # ensure the lock will be removed
            self.release()


    def lock(self):
        '''
        locking function, if lock is present it will raise LockHeld exception
        '''
        lockname = '%s' % (os.getpid())

        self.trylock()
        self.makelock(lockname, self.pidfile)
        return True

    def trylock(self):
        running_pid = False
        try:
            pidfile = open(self.pidfile, "r")
            pidfile.seek(0)
            running_pid = pidfile.readline()
            if self.debug:
                print 'lock file present running_pid: %s, checking for execution'\
                % running_pid
            # Now we check the PID from lock file matches to the current
            # process PID
            if running_pid:
                if os.path.exists("/proc/%s" % running_pid):
                        print "You already have an instance of the program running"
                        print "It is running as process %s" % running_pid
                        raise LockHeld
                else:
                        print "Lock File is there but the program is not running"
                        print "Removing lock file for the: %s" % running_pid
                        self.release()
        except IOError, e:
            if e.errno != 2:
                raise


    def release(self):
        '''
        releases the pid by removing the pidfile
        '''
        if self.callbackfn:
            #execute callback function on release
            if self.debug:
                print 'executing callback function %s' % self.callbackfn
            self.callbackfn()
        try:
            if self.debug:
                print 'removing pidfile %s' % self.pidfile
            os.remove(self.pidfile)
            self.held = False
        except OSError, e:
            if self.debug:
                print 'removing pidfile failed %s' % e
            pass

    def makelock(self, lockname, pidfile):
        '''
        this function will make an actual lock
        @param lockname: acctual pid of file
        @param pidfile: the file to write the pid in
        '''
        if self.debug:
            print 'creating a file %s and pid: %s' % (pidfile, lockname)
        pidfile = open(self.pidfile, "wb")
        pidfile.write(lockname)
        pidfile.close
        self.held = True


def main():
    print 'func is running'
    cnt = 20
    while 1:
        print cnt
        if cnt == 0:
            break
        time.sleep(1)
        cnt -= 1


if __name__ == "__main__":
    try:
        l = DaemonLock(desc='test lock')
        main()
        l.release()
    except LockHeld:
        sys.exit(1)
