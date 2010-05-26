import logging
from os.path import dirname as dn
from sqlalchemy.engine import create_engine
import os
from pylons_app.model.db import Users
from pylons_app.model.meta import Session

from pylons_app.lib.auth import get_crypt_password
from pylons_app.model import init_model

ROOT = dn(dn(dn(os.path.realpath(__file__))))
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s')
from pylons_app.model.meta import Base

class DbManage(object):
    def __init__(self):
        dburi = 'sqlite:////%s' % os.path.join(ROOT, 'hg_app.db')
        engine = create_engine(dburi) 
        init_model(engine)
        self.sa = Session()
    
    def check_for_db(self, override):
        if not override:
            if os.path.isfile(os.path.join(ROOT, 'hg_app.db')):
                raise Exception('database already exists')
    
    def create_tables(self, override=False):
        """
        Create a auth database
        """
        self.check_for_db(override)
                
        Base.metadata.create_all(checkfirst=override)
        logging.info('Created tables')
    
    def admin_prompt(self):
        import getpass
        username = raw_input('give admin username:')
        password = getpass.getpass('Specify admin password:')
        self.create_user(username, password, True)
        
    def create_user(self, username, password, admin=False):
        logging.info('creating user %s', username)
        
        new_user = Users()
        new_user.username = username
        new_user.password = get_crypt_password(password)
        new_user.admin = admin
        new_user.active = True
        
        try:
            self.sa.add(new_user)
            self.sa.commit()
        except:
            self.sa.rollback()
            raise
    
if __name__ == '__main__':
    dbmanage = DbManage()
    dbmanage.create_tables(override=True)
    dbmanage.admin_prompt()  


