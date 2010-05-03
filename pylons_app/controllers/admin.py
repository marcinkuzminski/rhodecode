import logging

from pylons import request, response, session, tmpl_context as c, url, app_globals as g
from pylons.controllers.util import abort, redirect

from pylons_app.lib.base import BaseController, render
import os
from pylons_app.lib import auth
from pylons_app.model.forms import LoginForm
import formencode
import formencode.htmlfill as htmlfill
from pylons_app.model import meta
from pylons_app.model.db import Users, UserLogs
from webhelpers.paginate import Page
from pylons_app.lib.utils import check_repo
log = logging.getLogger(__name__)

class AdminController(BaseController):

    def __before__(self):
        
        c.admin_user = session.get('admin_user', False)
        c.admin_username = session.get('admin_username')
        
    def index(self):
        # Return a rendered template
        if request.POST:
            #import Login Form validator class
            login_form = LoginForm()

            try:
                c.form_result = login_form.to_python(dict(request.params))
                if auth.admin_auth(c.form_result['username'], c.form_result['password']):
                    session['admin_user'] = True
                    session['admin_username'] = c.form_result['username']
                    session.save()
                    return redirect(url('admin_home'))
                else:
                    raise formencode.Invalid('Login Error', None, None,
                                             error_dict={'username':'invalid login',
                                                         'password':'invalid password'})
                                      
            except formencode.Invalid, error:
                c.form_result = error.value
                c.form_errors = error.error_dict or {}
                html = render('admin/admin.html')

                return htmlfill.render(
                    html,
                    defaults=c.form_result,
                    encoding="UTF-8"
                )
        if c.admin_user:
            sa = meta.Session
                             
            users_log = sa.query(UserLogs)\
                .order_by(UserLogs.action_date.desc())
            p = int(request.params.get('page', 1))
            c.users_log = Page(users_log, page=p, items_per_page=10)
            c.log_data = render('admin/admin_log.html')
            if request.params.get('partial'):
                return c.log_data
        return render('admin/admin.html')

    def hgrc(self, dirname):
        filename = os.path.join(dirname, '.hg', 'hgrc')
        return filename

    def add_repo(self, new_repo):
        

        #extra check it can be add since it's the command
        if new_repo == '_admin':
            c.msg = 'DENIED'
            c.new_repo = ''
            return render('add.html')

        new_repo = new_repo.replace(" ", "_")
        new_repo = new_repo.replace("-", "_")

        try:
            self._create_repo(new_repo)
            c.new_repo = new_repo
            c.msg = 'added repo'
        except Exception as e:
            c.new_repo = 'Exception when adding: %s' % new_repo
            c.msg = str(e)

        return render('add.html')


    def _create_repo(self, repo_name):
        if repo_name in [None, '', 'add']:
            raise Exception('undefined repo_name of repo')

        if check_repo(repo_name, g.base_path):
            log.info('creating repo %s in %s', repo_name, self.repo_path)
            cmd = """mkdir %s && hg init %s""" \
                    % (self.repo_path, self.repo_path)
            os.popen(cmd)
