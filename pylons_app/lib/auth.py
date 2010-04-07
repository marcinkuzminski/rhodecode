import sqlite3
import os
import logging
from os.path import dirname as dn
from datetime import datetime
import crypt

log = logging.getLogger(__name__)
ROOT = dn(dn(dn(os.path.realpath(__file__))))

def get_sqlite_cur_conn():
    conn = sqlite3.connect(os.path.join(ROOT, 'auth.sqlite'))
    cur = conn.cursor()
    return conn, cur

def authfunc(environ, username, password):
    conn, cur = get_sqlite_cur_conn()
    password_crypt = crypt.crypt(password, '6a')

    try:
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        data = cur.fetchone()
    except sqlite3.OperationalError as e:
        data = None
        log.error(e)

    if data:
        if data[3]:
            if data[1] == username and data[2] == password_crypt:
                log.info('user %s authenticated correctly', username)
                
                http_accept = environ.get('HTTP_ACCEPT')
        
                if http_accept.startswith('application/mercurial') or \
                    environ['PATH_INFO'].find('raw-file') != -1:
                    cmd = environ['PATH_INFO']
                    for qry in environ['QUERY_STRING'].split('&'):
                        if qry.startswith('cmd'):
                            cmd += "|" + qry
                            
                            try:
                                cur.execute('''INSERT INTO 
                                                    user_logs 
                                               VALUES(?,?,?,?)''',
                                                (None, data[0], cmd, datetime.now()))
                                conn.commit()
                            except Exception as e:
                                conn.rollback()
                                log.error(e)
                            
                                
                return True
        else:
            log.error('user %s is disabled', username)
            
    return False

def create_user_table():
    '''
    Create a auth database
    '''
    conn, cur = get_sqlite_cur_conn()
    try:
        log.info('creating table %s', 'users')
        cur.execute('''DROP TABLE IF EXISTS users ''')
        cur.execute('''CREATE TABLE users
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         username TEXT, 
                         password TEXT,
                         active INTEGER)''')
        log.info('creating table %s', 'user_logs')
        cur.execute('''DROP TABLE IF EXISTS user_logs ''')
        cur.execute('''CREATE TABLE user_logs
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            last_action TEXT, 
                            last_action_date DATETIME)''')
        conn.commit()
    except:
        conn.rollback()
        raise
    
    cur.close()
    
def create_user(username, password):
    conn, cur = get_sqlite_cur_conn()    
    password_crypt = crypt.crypt(password, '6a')
    cur_date = datetime.now()
    log.info('creating user %s', username)
    try:
        cur.execute('''INSERT INTO users values (?,?,?,?) ''',
                    (None, username, password_crypt, 1,))     
        conn.commit()
    except:
        conn.rollback()
        raise
    
if __name__ == "__main__":
    create_user_table()
    create_user('marcink', 'qweqwe')
    create_user('lukaszd', 'qweqwe')
    create_user('adriand', 'qweqwe')
    create_user('radek', 'qweqwe')
    create_user('skrzeka', 'qweqwe')
    create_user('bart', 'qweqwe')
    create_user('maho', 'qweqwe')
    create_user('michalg', 'qweqwe')
    
    #authfunc('', 'marcink', 'qweqwe')
