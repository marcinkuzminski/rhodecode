from sqlalchemy.interfaces import ConnectionProxy
import time
import logging
log = logging.getLogger('timerproxy')
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = xrange(30, 38)

def color_sql(sql):
    COLOR_SEQ = "\033[1;%dm"
    COLOR_SQL = YELLOW
    normal = '\x1b[0m'
    return COLOR_SEQ % COLOR_SQL + sql + normal 

def format_sql(sql):
    sql = color_sql(sql)
    sql = sql.replace('SELECT', '\n    SELECT \n\t')\
        .replace('FROM', '\n    FROM')\
        .replace('ORDER BY', '\n    ORDER BY')\
        .replace('LIMIT', '\n    LIMIT')\
        .replace('WHERE', '\n    WHERE')\
        .replace('AND', '\n    AND')\
        .replace('LEFT', '\n    LEFT')\
        .replace('INNER', '\n    INNER')\
        .replace('INSERT', '\n    INSERT')\
        .replace('DELETE', '\n    DELETE')
    return sql


class TimerProxy(ConnectionProxy):
    def cursor_execute(self, execute, cursor, statement, parameters, context, executemany):
        now = time.time()
        try:
            log.info(">>>>> STARTING QUERY >>>>>")
            return execute(cursor, statement, parameters, context)
        finally:
            total = time.time() - now
            try:
                log.info(format_sql("Query: %s" % statement % parameters))
            except TypeError:
                log.info(format_sql("Query: %s %s" % (statement, parameters)))
            log.info("<<<<< TOTAL TIME: %f <<<<<" % total)




