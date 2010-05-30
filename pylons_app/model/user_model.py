#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 marcink.  All rights reserved.
#
from pylons_app.model.db import User
from pylons_app.model.meta import Session
'''
Created on Apr 9, 2010

@author: marcink
'''

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
        except:
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
        except:
            self.sa.rollback()
            raise      
