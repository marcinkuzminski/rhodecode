from sqlalchemy.interfaces import ConnectionProxy
import time
from sqlalchemy import log
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
        .replace('UPDATE', '\n\tUPDATE \n\t')\
        .replace('DELETE', '\n\tDELETE \n\t')\
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
    
    def __init__(self):
        super(TimerProxy, self).__init__()
        self.logging_name = 'timerProxy'
        self.log = log.instance_logger(self, True)
        
    def cursor_execute(self, execute, cursor, statement, parameters, context, executemany):
        
        now = time.time()
        try:
            self.log.info(">>>>> STARTING QUERY >>>>>")
            return execute(cursor, statement, parameters, context)
        finally:
            total = time.time() - now
            try:
                self.log.info(format_sql("Query: %s" % statement % parameters))
            except TypeError:
                self.log.info(format_sql("Query: %s %s" % (statement, parameters)))
            self.log.info("<<<<< TOTAL TIME: %f <<<<<" % total)
