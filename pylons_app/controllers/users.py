from formencode import htmlfill
from pylons import request, response, session, tmpl_context as c, url, \
    app_globals as g
from pylons.i18n.translation import _
from pylons_app.lib import helpers as h    
from pylons.controllers.util import abort, redirect
from pylons_app.lib.auth import LoginRequired, CheckPermissionAll
from pylons_app.lib.base import BaseController, render
from pylons_app.model.db import User, UserLog
from pylons_app.model.forms import UserForm
from pylons_app.model.user_model import UserModel
import formencode
import logging



log = logging.getLogger(__name__)

class UsersController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('user', 'users')
    @LoginRequired()
    def __before__(self):
        c.admin_user = session.get('admin_user')
        c.admin_username = session.get('admin_username')
        super(UsersController, self).__before__()
    

    def index(self, format='html'):
        """GET /users: All items in the collection"""
        # url('users')
        
        c.users_list = self.sa.query(User).all()     
        return render('admin/users/users.html')
    
    def create(self):
        """POST /users: Create a new item"""
        # url('users')
        
        user_model = UserModel()
        login_form = UserForm()()
        try:
            form_result = login_form.to_python(dict(request.POST))
            user_model.create(form_result)
            h.flash(_('created user %s') % form_result['username'], category='success')
            return redirect(url('users'))
                           
        except formencode.Invalid as errors:
            c.form_errors = errors.error_dict
            return htmlfill.render(
                 render('admin/users/user_add.html'),
                defaults=errors.value,
                encoding="UTF-8")
    
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
        user_model = UserModel()
        login_form = UserForm(edit=True)()
        try:
            form_result = login_form.to_python(dict(request.POST))
            user_model.update(id, form_result)
            h.flash(_('User updated succesfully'), category='success')
            return redirect(url('users'))
                           
        except formencode.Invalid as errors:
            c.user = user_model.get_user(id)
            c.form_errors = errors.error_dict
            return htmlfill.render(
                 render('admin/users/user_edit.html'),
                defaults=errors.value,
                encoding="UTF-8")
    
    def delete(self, id):
        """DELETE /users/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('user', id=ID),
        #           method='delete')
        # url('user', id=ID)
        try:
            self.sa.delete(self.sa.query(User).get(id))
            self.sa.commit()
            h.flash(_('sucessfully deleted user'), category='success')
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
        c.user = self.sa.query(User).get(id)
        defaults = c.user.__dict__
        return htmlfill.render(
            render('admin/users/user_edit.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )    
