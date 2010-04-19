from sqlalchemy.interfaces import ConnectionProxy
import time
import logging
log = logging.getLogger('timerproxy')

class TimerProxy(ConnectionProxy):
    def cursor_execute(self, execute, cursor, statement, parameters, context, executemany):
        now = time.time()
        try:
            log.info(">>>>> STARTING QUERY >>>>>")
            return execute(cursor, statement, parameters, context)
        finally:
            total = time.time() - now
            try:
                log.info("Query: %s" % statement % parameters)
            except TypeError:
                log.info("Query: %s %s" % (statement, parameters))
            log.info("<<<<< TOTAL TIME: %f <<<<<" % total)
