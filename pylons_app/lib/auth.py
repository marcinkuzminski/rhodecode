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
from pylons import session, url, request
from pylons.controllers.util import abort, redirect
from pylons_app.model import meta
from pylons_app.model.db import User, Repo2Perm, Repository, Permission
from pylons_app.lib.utils import get_repo_slug
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import crypt
import logging
from pylons import config
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
    def __init__(self):
        self.username = 'None'
        self.user_id = None
        self.is_authenticated = False
        self.is_admin = False
        self.permissions = {}


def set_available_permissions(config):
    """
    This function will propagate pylons globals with all available defined
    permission given in db. We don't wannt to check each time from db for new 
    permissions since adding a new permission also requires application restart
    ie. to decorate new views with the newly created permission
    @param config:
    """
    log.info('getting information about all available permissions')
    sa = meta.Session
    all_perms = sa.query(Permission).all()
    config['available_permissions'] = [x.permission_name for x in all_perms]

def set_base_path(config):
    config['base_path'] = config['pylons.app_globals'].base_path
        
def fill_perms(user):
    sa = meta.Session
    user.permissions['repositories'] = {}
    
    #first fetch default permissions
    default_perms = sa.query(Repo2Perm, Repository, Permission)\
        .join((Repository, Repo2Perm.repository == Repository.repo_name))\
        .join((Permission, Repo2Perm.permission_id == Permission.permission_id))\
        .filter(Repo2Perm.user_id == sa.query(User).filter(User.username == 
                                            'default').one().user_id).all()

    if user.is_admin:
        user.permissions['global'] = set(['hg.admin'])
        #admin have all rights full
        for perm in default_perms:
            p = 'repository.admin'
            user.permissions['repositories'][perm.Repo2Perm.repository] = p
    
    else:
        user.permissions['global'] = set()
        for perm in default_perms:
            if perm.Repository.private:
                #disable defaults for private repos,
                p = 'repository.none'
            elif perm.Repository.user_id == user.user_id:
                #set admin if owner
                p = 'repository.admin'
            else:
                p = perm.Permission.permission_name
                
            user.permissions['repositories'][perm.Repo2Perm.repository] = p
                                                
        
        user_perms = sa.query(Repo2Perm, Permission, Repository)\
            .join((Repository, Repo2Perm.repository == Repository.repo_name))\
            .join((Permission, Repo2Perm.permission_id == Permission.permission_id))\
            .filter(Repo2Perm.user_id == user.user_id).all()
        #overwrite userpermissions with defaults
        for perm in user_perms:
            #set write if owner
            if perm.Repository.user_id == user.user_id:
                p = 'repository.write'
            else:
                p = perm.Permission.permission_name
            user.permissions['repositories'][perm.Repo2Perm.repository] = p            
    return user
    
def get_user(session):
    """
    Gets user from session, and wraps permissions into user
    @param session:
    """
    user = session.get('hg_app_user', AuthUser())
        
    if user.is_authenticated:
        user = fill_perms(user)

    session['hg_app_user'] = user
    session.save()
    return user
        
#===============================================================================
# CHECK DECORATORS
#===============================================================================
class LoginRequired(object):
    """
    Must be logged in to execute this function else redirect to login page
    """
   
    def __call__(self, func):
        @wraps(func)
        def _wrapper(*fargs, **fkwargs):
            user = session.get('hg_app_user', AuthUser())
            log.debug('Checking login required for user:%s', user.username)
            if user.is_authenticated:
                log.debug('user %s is authenticated', user.username)
                func(*fargs)
            else:
                log.warn('user %s not authenticated', user.username)
                log.debug('redirecting to login page')
                return redirect(url('login_home'))

        return _wrapper

class PermsDecorator(object):
    """
    Base class for decorators
    """
    
    def __init__(self, *required_perms):
        available_perms = config['available_permissions']
        for perm in required_perms:
            if perm not in available_perms:
                raise Exception("'%s' permission is not defined" % perm)
        self.required_perms = set(required_perms)
        self.user_perms = None
        
    def __call__(self, func):
        @wraps(func)
        def _wrapper(*fargs, **fkwargs):
            self.user_perms = session.get('hg_app_user', AuthUser()).permissions
            log.debug('checking %s permissions %s for %s',
               self.__class__.__name__, self.required_perms, func.__name__)
            
            if self.check_permissions():
                log.debug('Permission granted for %s', func.__name__)
                return func(*fargs)
            
            else:
                log.warning('Permission denied for %s', func.__name__)
                #redirect with forbidden ret code
                return abort(403)
        return _wrapper
        
        
    def check_permissions(self):
        """
        Dummy function for overriding
        """
        raise Exception('You have to write this function in child class')

class HasPermissionAllDecorator(PermsDecorator):
    """
    Checks for access permission for all given predicates. All of them have to
    be meet in order to fulfill the request
    """
        
    def check_permissions(self):
        if self.required_perms.issubset(self.user_perms['global']):
            return True
        return False
            

class HasPermissionAnyDecorator(PermsDecorator):
    """
    Checks for access permission for any of given predicates. In order to 
    fulfill the request any of predicates must be meet
    """
    
    def check_permissions(self):
        if self.required_perms.intersection(self.user_perms['global']):
            return True
        return False

class HasRepoPermissionAllDecorator(PermsDecorator):
    """
    Checks for access permission for all given predicates for specific 
    repository. All of them have to be meet in order to fulfill the request
    """
            
    def check_permissions(self):
        repo_name = get_repo_slug(request)
        user_perms = set([self.user_perms['repositories'][repo_name]])
        if self.required_perms.issubset(user_perms):
            return True
        return False
            

class HasRepoPermissionAnyDecorator(PermsDecorator):
    """
    Checks for access permission for any of given predicates for specific 
    repository. In order to fulfill the request any of predicates must be meet
    """
            
    def check_permissions(self):
        repo_name = get_repo_slug(request)
        
        user_perms = set([self.user_perms['repositories'][repo_name]])
        if self.required_perms.intersection(user_perms):
            return True
        return False
#===============================================================================
# CHECK FUNCTIONS
#===============================================================================

class PermsFunction(object):
    """
    Base function for other check functions
    """
    
    def __init__(self, *perms):
        available_perms = config['available_permissions']
        
        for perm in perms:
            if perm not in available_perms:
                raise Exception("'%s' permission in not defined" % perm)
        self.required_perms = set(perms)
        self.user_perms = None
        self.granted_for = ''
        self.repo_name = None
        
    def __call__(self, check_Location=''):
        user = session.get('hg_app_user', False)
        if not user:
            return False
        self.user_perms = user.permissions
        self.granted_for = user.username        
        log.debug('checking %s %s', self.__class__.__name__, self.required_perms)            
        
        if self.check_permissions():
            log.debug('Permission granted for %s @%s', self.granted_for,
                      check_Location)
            return True
        
        else:
            log.warning('Permission denied for %s @%s', self.granted_for,
                        check_Location)
            return False 
    
    def check_permissions(self):
        """
        Dummy function for overriding
        """
        raise Exception('You have to write this function in child class')
        
class HasPermissionAll(PermsFunction):
    def check_permissions(self):
        if self.required_perms.issubset(self.user_perms['global']):
            return True
        return False

class HasPermissionAny(PermsFunction):
    def check_permissions(self):
        if self.required_perms.intersection(self.user_perms['global']):
            return True
        return False

class HasRepoPermissionAll(PermsFunction):
    
    def __call__(self, repo_name=None, check_Location=''):
        self.repo_name = repo_name
        return super(HasRepoPermissionAll, self).__call__(check_Location)
            
    def check_permissions(self):
        if not self.repo_name:
            self.repo_name = get_repo_slug(request)

        self.user_perms = set([self.user_perms['repositories']\
                               .get(self.repo_name)])
        self.granted_for = self.repo_name       
        if self.required_perms.issubset(self.user_perms):
            return True
        return False
            
class HasRepoPermissionAny(PermsFunction):
    
    
    def __call__(self, repo_name=None, check_Location=''):
        self.repo_name = repo_name
        return super(HasRepoPermissionAny, self).__call__(check_Location)
        
    def check_permissions(self):
        if not self.repo_name:
            self.repo_name = get_repo_slug(request)

        self.user_perms = set([self.user_perms['repositories']\
                               .get(self.repo_name)])
        self.granted_for = self.repo_name
        if self.required_perms.intersection(self.user_perms):
            return True
        return False

#===============================================================================
# SPECIAL VERSION TO HANDLE MIDDLEWARE AUTH
#===============================================================================

class HasPermissionAnyMiddleware(object):
    def __init__(self, *perms):
        self.required_perms = set(perms)
    
    def __call__(self, user, repo_name):
        usr = AuthUser()
        usr.user_id = user.user_id
        usr.username = user.username
        usr.is_admin = user.admin
        
        try:
            self.user_perms = set([fill_perms(usr)\
                                   .permissions['repositories'][repo_name]])
        except:
            self.user_perms = set()
        self.granted_for = ''
        self.username = user.username
        self.repo_name = repo_name        
        return self.check_permissions()
            
    def check_permissions(self):
        log.debug('checking mercurial protocol '
                  'permissions for user:%s repository:%s',
                                                self.username, self.repo_name)
        if self.required_perms.intersection(self.user_perms):
            log.debug('permission granted')
            return True
        log.debug('permission denied')
        return False
