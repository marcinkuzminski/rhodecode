from datetime import datetime
from decorator import decorator
from functools import wraps
from pylons import session, url
from pylons.controllers.util import abort, redirect
from pylons_app.model import meta
from pylons_app.model.db import Users
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import crypt
import logging
log = logging.getLogger(__name__)

def get_crypt_password(password):
    """
    Cryptographic function used for password hashing
    @param password: password to hash
    """
    return crypt.crypt(password, '6a')

def authfunc(environ, username, password):
    sa = meta.Session
    password_crypt = get_crypt_password(password)
    try:
        user = sa.query(Users).filter(Users.username == username).one()
    except (NoResultFound, MultipleResultsFound, OperationalError) as e:
        log.error(e)
        user = None
        
    if user:
        if user.active:
            if user.username == username and user.password == password_crypt:
                log.info('user %s authenticated correctly', username)
                return True
        else:
            log.error('user %s is disabled', username)
            
    return False

class  AuthUser(object):
    """
    A simple object that handles a mercurial username for authentication
    """
    username = 'Empty'
    is_authenticated = False
    is_admin = False
    permissions = set()
    group = set()
    
    def __init__(self):
        pass
    
#===============================================================================
# DECORATORS
#===============================================================================
class LoginRequired(object):
    """
    Must be logged in to execute this function else redirect to login page
    """
    def __init__(self):
        pass
    
    def __call__(self, func):
        user = session.get('hg_app_user', AuthUser())
        log.info('Checking login required for %s', user.username)
        
        @wraps(func)
        def _wrapper(*fargs, **fkwargs):
            if user.is_authenticated:
                    log.info('user %s is authenticated', user.username)
                    func(*fargs)
            else:
                logging.info('user %s not authenticated', user.username)
                return redirect(url('login_home'))

        return _wrapper
