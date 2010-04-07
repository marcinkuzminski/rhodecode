from sqlalchemy.interfaces import ConnectionProxy
import time
import logging
log = logging.getLogger(__name__)

class TimerProxy(ConnectionProxy):
    def cursor_execute(self, execute, cursor, statement, parameters, context, executemany):
        now = time.time()
        try:
            log.info(">>>>> STARTING QUERY >>>>>")
            return execute(cursor, statement, parameters, context)
        finally:
            total = time.time() - now
            log.info("Query: %s" % statement % parameters)
            log.info("<<<<< TOTAL TIME: %f <<<<<" % total)
