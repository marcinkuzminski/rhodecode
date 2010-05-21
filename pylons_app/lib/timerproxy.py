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

def one_space_trim(s):
    if s.find("  ") == -1:
        return s
    else:
        s = s.replace('  ', ' ')
        return one_space_trim(s)
    
def format_sql(sql):
    sql = color_sql(sql)
    sql = sql.replace('\n', '')
    sql = one_space_trim(sql)
    sql = sql\
        .replace('SELECT', '\n\tSELECT \n\t')\
        .replace('FROM', '\n\tFROM')\
        .replace('ORDER BY', '\n\tORDER BY')\
        .replace('LIMIT', '\n\tLIMIT')\
        .replace('WHERE', '\n\tWHERE')\
        .replace('AND', '\n\tAND')\
        .replace('LEFT', '\n\tLEFT')\
        .replace('INNER', '\n\tINNER')\
        .replace('INSERT', '\n\tINSERT')\
        .replace('DELETE', '\n\tDELETE')
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




