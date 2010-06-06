#!/usr/bin/env python
# encoding: utf-8
# authentication and permission libraries
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your opinion) any later version of the license.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.
"""
Created on April 4, 2010

@author: marcink
"""

from functools import wraps
from pylons import session, url, app_globals as g
from pylons.controllers.util import abort, redirect
from pylons_app.model import meta
from pylons_app.model.db import User
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
        user = sa.query(User).filter(User.username == username).one()
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
    username = 'None'
    user_id = None
    is_authenticated = False
    is_admin = False
    permissions = set()
    group = set()
    
    def __init__(self):
        pass



def set_available_permissions(config):
    """
    This function will propagate pylons globals with all available defined
    permission given in db. We don't wannt to check each time from db for new 
    permissions since adding a new permission also requires application restart
    ie. to decorate new views with the newly created permission
    @param config:
    """
    from pylons_app.model.meta import Session
    from pylons_app.model.db import Permission
    logging.info('getting information about all available permissions')
    sa = Session()
    all_perms = sa.query(Permission).all()
    config['pylons.app_globals'].available_permissions = [x.permission_name for x in all_perms]


        
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
        
        @wraps(func)
        def _wrapper(*fargs, **fkwargs):
            user = session.get('hg_app_user', AuthUser())
            log.info('Checking login required for user:%s', user.username)            
            if user.is_authenticated:
                    log.info('user %s is authenticated', user.username)
                    func(*fargs)
            else:
                logging.info('user %s not authenticated', user.username)
                logging.info('redirecting to login page')
                return redirect(url('login_home'))

        return _wrapper

class PermsDecorator(object):
    
    def __init__(self, *perms):
        available_perms = g.available_permissions
        for perm in perms:
            if perm not in available_perms:
                raise Exception("'%s' permission in not defined" % perm)
        self.required_perms = set(perms)
        self.user_perms = set([])#propagate this list from somewhere.
        
    def __call__(self, func):        
        @wraps(func)
        def _wrapper(*args, **kwargs):
            logging.info('checking %s permissions %s for %s',
               self.__class__.__name__[-3:], self.required_perms, func.__name__)            
            
            if self.check_permissions():
                logging.info('Permission granted for %s', func.__name__)
                return func(*args, **kwargs)
            
            else:
                logging.warning('Permission denied for %s', func.__name__)
                #redirect with forbidden ret code
                return redirect(url('access_denied'), 403) 
        return _wrapper
        
        
    def check_permissions(self):
        """
        Dummy function for overiding
        """
        raise Exception('You have to write this function in child class')

class CheckPermissionAll(PermsDecorator):
    """
    Checks for access permission for all given predicates. All of them have to
    be meet in order to fulfill the request
    """
        
    def check_permissions(self):
        if self.required_perms.issubset(self.user_perms):
            return True
        return False
            

class CheckPermissionAny(PermsDecorator):
    """
    Checks for access permission for any of given predicates. In order to 
    fulfill the request any of predicates must be meet
    """
    
    def check_permissions(self):
        if self.required_perms.intersection(self.user_perms):
            return True
        return False



