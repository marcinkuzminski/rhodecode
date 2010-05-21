import logging
import os

from pylons import request, response, session, tmpl_context as c, url, app_globals as g
from pylons.controllers.util import abort, redirect
from pylons_app.lib.base import BaseController, render
from pylons_app.model import meta
from pylons_app.model.db import UserLogs
from webhelpers.paginate import Page
from pylons_app.lib.utils import check_repo, invalidate_cache
from pylons_app.lib.auth import LoginRequired

log = logging.getLogger(__name__)

class AdminController(BaseController):
    
    @LoginRequired()
    def __before__(self):
        user = session['hg_app_user']
        c.admin_user = user.is_admin
        c.admin_username = user.username
        super(AdminController, self).__before__()
        
    def index(self):
        sa = meta.Session
                         
        users_log = sa.query(UserLogs)\
            .order_by(UserLogs.action_date.desc())
        p = int(request.params.get('page', 1))
        c.users_log = Page(users_log, page=p, items_per_page=10)
        c.log_data = render('admin/admin_log.html')
        if request.params.get('partial'):
            return c.log_data
        return render('admin/admin.html')

    def add_repo(self, new_repo):
        #extra check it can be add since it's the command
        if new_repo == '_admin':
            c.msg = 'DENIED'
            c.new_repo = ''
            return render('admin/add.html')

        new_repo = new_repo.replace(" ", "_")
        new_repo = new_repo.replace("-", "_")

        try:
            self._create_repo(new_repo)
            c.new_repo = new_repo
            c.msg = 'added repo'
            #clear our cached list for refresh with new repo
            invalidate_cache('cached_repo_list')
        except Exception as e:
            c.new_repo = 'Exception when adding: %s' % new_repo
            c.msg = str(e)

        return render('admin/add.html')


    def _create_repo(self, repo_name):
        if repo_name in [None, '', 'add']:
            raise Exception('undefined repo_name of repo')
        repo_path = os.path.join(g.base_path, repo_name)
        if check_repo(repo_name, g.base_path):
            log.info('creating repo %s in %s', repo_name, repo_path)
            from vcs.backends.hg import MercurialRepository
            MercurialRepository(repo_path, create=True)        
                
