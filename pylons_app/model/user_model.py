#!/usr/bin/env python
# encoding: utf-8
# Model for users
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
Created on April 9, 2010
Model for users
@author: marcink
"""

from pylons_app.model.db import User
from pylons_app.model.meta import Session
import logging
log = logging.getLogger(__name__)

class UserModel(object):

    def __init__(self):
        self.sa = Session() 
    
    def get_user(self, id):
        return self.sa.query(User).get(id)
    
    def create(self, form_data):
        try:
            new_user = User()
            for k, v in form_data.items():
                setattr(new_user, k, v)
                
            self.sa.add(new_user)
            self.sa.commit()
        except Exception as e:
            log.error(e)
            self.sa.rollback()
            raise      
    
    def update(self, id, form_data):
        try:
            new_user = self.sa.query(User).get(id)
            for k, v in form_data.items():
                if k == 'new_password' and v != '':
                    
                    new_user.password = v
                else:
                    setattr(new_user, k, v)
                
            self.sa.add(new_user)
            self.sa.commit()
        except Exception as e:
            log.error(e)
            self.sa.rollback()
            raise      

    def delete(self, id):
        try:
            self.sa.delete(self.sa.query(User).get(id))
            self.sa.commit()            
        except Exception as e:
            log.error(e)
            self.sa.rollback()
            raise        
