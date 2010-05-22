import logging
from formencode import htmlfill
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons_app.lib.base import BaseController, render
import formencode
from pylons_app.model.forms import LoginForm
from pylons_app.lib.auth import AuthUser

log = logging.getLogger(__name__)

class LoginController(BaseController):

    def index(self):
        #redirect if already logged in
        if c.hg_app_user.is_authenticated:
            return redirect(url('hg_home'))
        
        if request.POST:
            #import Login Form validator class
            login_form = LoginForm()
            try:
                c.form_result = login_form.to_python(dict(request.POST))
                return redirect(url('hg_home'))
                               
            except formencode.Invalid as errors:
                c.form_errors = errors.error_dict
                return htmlfill.render(
                    render('/login.html'),
                    defaults=errors.value,
                    encoding="UTF-8")
                        
        return render('/login.html')
    
    def logout(self):
        session['hg_app_user'] = AuthUser()
        session.save()
        redirect(url('hg_home'))
