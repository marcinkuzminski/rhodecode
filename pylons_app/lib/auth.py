import logging
from datetime import datetime
import crypt
from pylons import session, url
from pylons.controllers.util import abort, redirect
from decorator import decorator
from sqlalchemy.exc import OperationalError
log = logging.getLogger(__name__)
from pylons_app.model import meta
from pylons_app.model.db import Users, UserLogs
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

def get_crypt_password(password):
    return crypt.crypt(password, '6a')

def admin_auth(username, password):
    sa = meta.Session
    password_crypt = get_crypt_password(password)

    try:
        user = sa.query(Users).filter(Users.username == username).one()
    except (NoResultFound, MultipleResultsFound, OperationalError) as e:
        log.error(e)
        user = None
        
    if user:
        if user.active:
            if user.username == username and user.password == password_crypt and user.admin:
                log.info('user %s authenticated correctly', username)
                return True
        else:
            log.error('user %s is disabled', username)
            
    return False

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
                if environ:
                    http_accept = environ.get('HTTP_ACCEPT')
            
                    if http_accept.startswith('application/mercurial') or \
                        environ['PATH_INFO'].find('raw-file') != -1:
                        repo = environ['PATH_INFO']
                        for qry in environ['QUERY_STRING'].split('&'):
                            if qry.startswith('cmd'):
                                
                                try:
                                    user_log = UserLogs()
                                    user_log.user_id = user.user_id
                                    user_log.action = qry
                                    user_log.repository = repo
                                    user_log.action_date = datetime.now()
                                    sa.add(user_log)
                                    sa.commit()
                                    log.info('Adding user %s, action %s', username, qry)
                                except Exception as e:
                                    sa.rollback()
                                    log.error(e)
                                  
                return True
        else:
            log.error('user %s is disabled', username)
            
    return False


@decorator
def authenticate(fn, *args, **kwargs):
    if not session.get('admin_user', False):
        redirect(url('admin_home'), 301)
    return fn(*args, **kwargs)

