import logging
import sqlite3 

import os
import crypt
from os.path import dirname as dn
ROOT = dn(dn(dn(os.path.realpath(__file__))))
logging.basicConfig(level=logging.DEBUG)

def get_sqlite_conn_cur():
    conn = sqlite3.connect(os.path.join(ROOT, 'hg_app.db'))
    cur = conn.cursor()
    return conn, cur

def check_for_db():
    if os.path.isfile(os.path.join(ROOT, 'hg_app.db')):
        raise Exception('database already exists')

def create_tables():
    """
    Create a auth database
    """
    check_for_db()
    conn, cur = get_sqlite_conn_cur()
    try:
        logging.info('creating table %s', 'users')
        cur.execute("""DROP TABLE IF EXISTS users """)
        cur.execute("""CREATE TABLE users
                        (user_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         username TEXT, 
                         password TEXT,
                         active INTEGER,
                         admin INTEGER)""")
        logging.info('creating table %s', 'user_logs')
        cur.execute("""DROP TABLE IF EXISTS user_logs """)
        cur.execute("""CREATE TABLE user_logs
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            repository TEXT,
                            action TEXT, 
                            action_date DATETIME)""")
        conn.commit()
    except:
        conn.rollback()
        raise
    
    cur.close()

def admin_prompt():
    import getpass
    username = raw_input('give username:')
    password = getpass.getpass('Specify admin password:')
    create_user(username, password, True)
    
def create_user(username, password, admin=False):
    conn, cur = get_sqlite_conn_cur()    
    password_crypt = crypt.crypt(password, '6a')
    logging.info('creating user %s', username)
    try:
        cur.execute("""INSERT INTO users values (?,?,?,?,?) """,
                    (None, username, password_crypt, 1, admin))     
        conn.commit()
    except:
        conn.rollback()
        raise
    
if __name__ == '__main__':
    create_tables()
    admin_prompt()  


