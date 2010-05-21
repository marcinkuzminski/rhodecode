import logging

from pylons import request, response, session, tmpl_context as c, url, app_globals as g
from pylons.controllers.util import abort, redirect

from pylons_app.lib.base import BaseController, render
from formencode import htmlfill
from pylons_app.model.db import Users, UserLogs
import crypt

log = logging.getLogger(__name__)

class UsersController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('user', 'users')
    
    def __before__(self):
        c.admin_user = session.get('admin_user')
        c.admin_username = session.get('admin_username')
        super(UsersController, self).__before__()
        
    def index(self, format='html'):
        """GET /users: All items in the collection"""
        # url('users')
        
        c.users_list = self.sa.query(Users).all()     
        return render('admin/users/users.html')
    
    def create(self):
        """POST /users: Create a new item"""
        # url('users')
        params = dict(request.params)

        try:
            new_user = Users()
            new_user.active = params.get('active', False)
            new_user.username = params.get('username')
            new_user.password = crypt.crypt(params.get('password'), '6a')
            new_user.admin = False
            self.sa.add(new_user)
            self.sa.commit()
        except:
            self.sa.rollback()
            raise      
          
        return redirect(url('users'))
    
    def new(self, format='html'):
        """GET /users/new: Form to create a new item"""
        # url('new_user')
        return render('admin/users/user_add.html')

    def update(self, id):
        """PUT /users/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('user', id=ID),
        #           method='put')
        # url('user', id=ID)
        params = dict(request.params)

        try:
            new_user = self.sa.query(Users).get(id)
            new_user.active = params.get('active', False)
            new_user.username = params.get('username')
            if params.get('new_password'):
                new_user.password = crypt.crypt(params.get('new_password'), '6a')
            self.sa.add(new_user)
            self.sa.commit()
        except:
            self.sa.rollback()
            raise      
          
        return redirect(url('users'))
    
    def delete(self, id):
        """DELETE /users/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('user', id=ID),
        #           method='delete')
        # url('user', id=ID)
        try:
            self.sa.delete(self.sa.query(Users).get(id))
            self.sa.commit()
        except:
            self.sa.rollback()
            raise
        return redirect(url('users'))
        
    def show(self, id, format='html'):
        """GET /users/id: Show a specific item"""
        # url('user', id=ID)
    
    
    def edit(self, id, format='html'):
        """GET /users/id/edit: Form to edit an existing item"""
        # url('edit_user', id=ID)
        c.user = self.sa.query(Users).get(id)
        defaults = c.user.__dict__
        return htmlfill.render(
            render('admin/users/user_edit.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )    
