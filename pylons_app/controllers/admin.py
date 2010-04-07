import logging

from pylons import request, response, session, tmpl_context as c, url, app_globals as g
from pylons.controllers.util import abort, redirect

from pylons_app.lib.base import BaseController, render
import os
from mercurial import ui, hg
from mercurial.error import RepoError
from ConfigParser import ConfigParser
from pylons_app.lib import auth
from pylons_app.model.forms import LoginForm
import formencode
import formencode.htmlfill as htmlfill
log = logging.getLogger(__name__)

class AdminController(BaseController):


    def __before__(self):
        c.staticurl = g.statics
        c.admin_user = session.get('admin_user')
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
                html = render('/admin.html')

                return htmlfill.render(
                    html,
                    defaults=c.form_result,
                    encoding="UTF-8"
                )
        return render('/admin.html')

    def repos_manage(self):
        return render('/repos_manage.html')
    
    def users_manage(self):
        conn, cur = auth.get_sqlite_conn_cur()
        cur.execute('SELECT * FROM users')
        c.users_list = cur.fetchall()        
        return render('/users_manage.html')
                
    def manage_hgrc(self):
        pass

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

    def _check_repo(self, repo_name):
        p = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        config_path = os.path.join(p, 'hgwebdir.config')

        cp = ConfigParser()

        cp.read(config_path)
        repos_path = cp.get('paths', '/').replace("**", '')

        if not repos_path:
            raise Exception('Could not read config !')

        self.repo_path = os.path.join(repos_path, repo_name)

        try:
            r = hg.repository(ui.ui(), self.repo_path)
            hg.verify(r)
            #here we hnow that repo exists it was verified
            log.info('%s repo is already created', repo_name)
            raise Exception('Repo exists')
        except RepoError:
            log.info('%s repo is free for creation', repo_name)
            #it means that there is no valid repo there...
            return True


    def _create_repo(self, repo_name):
        if repo_name in [None, '', 'add']:
            raise Exception('undefined repo_name of repo')

        if self._check_repo(repo_name):
            log.info('creating repo %s in %s', repo_name, self.repo_path)
            cmd = """mkdir %s && hg init %s""" \
                    % (self.repo_path, self.repo_path)
            os.popen(cmd)
