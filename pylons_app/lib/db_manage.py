import logging
import sqlite3 
log = logging.getLogger(__name__)
import os
import crypt
from os.path import dirname as dn
ROOT = dn(dn(dn(os.path.realpath(__file__))))

def get_sqlite_conn_cur():
    conn = sqlite3.connect(os.path.join(ROOT, 'auth.sqlite'))
    cur = conn.cursor()
    return conn, cur

def create_user_table():
    """
    Create a auth database
    """
    conn, cur = get_sqlite_conn_cur()
    try:
        log.info('creating table %s', 'users')
        cur.execute("""DROP TABLE IF EXISTS users """)
        cur.execute("""CREATE TABLE users
                        (user_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         username TEXT, 
                         password TEXT,
                         active INTEGER,
                         admin INTEGER)""")
        log.info('creating table %s', 'user_logs')
        cur.execute("""DROP TABLE IF EXISTS user_logs """)
        cur.execute("""CREATE TABLE user_logs
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            last_action TEXT, 
                            last_action_date DATETIME)""")
        conn.commit()
    except:
        conn.rollback()
        raise
    
    cur.close()
    
def create_user(username, password, admin=False):
    conn, cur = get_sqlite_conn_cur()    
    password_crypt = crypt.crypt(password, '6a')
    log.info('creating user %s', username)
    try:
        cur.execute("""INSERT INTO users values (?,?,?,?,?) """,
                    (None, username, password_crypt, 1, admin))     
        conn.commit()
    except:
        conn.rollback()
        raise
