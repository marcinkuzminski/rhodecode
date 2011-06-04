from sqlalchemy.interfaces import ConnectionProxy
import time
import logging
log = logging.getLogger('timerproxy')

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = xrange(30, 38)


def color_sql(sql):
    COLOR_SEQ = "\033[1;%dm"
    COLOR_SQL = YELLOW
    normal = '\x1b[0m'
    return ''.join([COLOR_SEQ % COLOR_SQL, sql, normal])


class TimerProxy(ConnectionProxy):

    def __init__(self):
        super(TimerProxy, self).__init__()

    def cursor_execute(self, execute, cursor, statement, parameters,
                       context, executemany):

        now = time.time()
        try:
            log.info(color_sql(">>>>> STARTING QUERY >>>>>"))
            return execute(cursor, statement, parameters, context)
        finally:
            total = time.time() - now
            log.info(color_sql("<<<<< TOTAL TIME: %f <<<<<" % total))
