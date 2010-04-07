import logging

from pylons import request, response, session, tmpl_context as c, url, app_globals as g
from pylons.controllers.util import abort, redirect

from pylons_app.lib.base import BaseController, render
from pylons_app.lib import auth
log = logging.getLogger(__name__)

class UsersController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('user', 'users')
    def __before__(self):
        c.staticurl = g.statics
        c.admin_user = session.get('admin_user')
        c.admin_username = session.get('admin_username')
        
    def index(self, format='html'):
        """GET /users: All items in the collection"""
        # url('users')
        conn, cur = auth.get_sqlite_conn_cur()
        cur.execute('SELECT * FROM users')
        c.users_list = cur.fetchall()        
        return render('/users_manage.html')
    
    def create(self):
        """POST /users: Create a new item"""
        # url('users')

    def new(self, format='html'):
        """GET /users/new: Form to create a new item"""
        # url('new_user')

    def update(self, id):
        """PUT /users/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('user', id=ID),
        #           method='put')
        # url('user', id=ID)

    def delete(self, id):
        """DELETE /users/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('user', id=ID),
        #           method='delete')
        # url('user', id=ID)

    def show(self, id, format='html'):
        """GET /users/id: Show a specific item"""
        # url('user', id=ID)

    def edit(self, id, format='html'):
        """GET /users/id/edit: Form to edit an existing item"""
        # url('edit_user', id=ID)
