from pylons import request, response, session, tmpl_context as c, url, \
    app_globals as g
from pylons.controllers.util import abort, redirect
from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import check_repo, invalidate_cache
import logging
import os
import shutil
from pylons_app.lib.filters import clean_repo
log = logging.getLogger(__name__)

class ReposController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('repo', 'repos')
    
    def __before__(self):
        c.admin_user = session.get('admin_user')
        c.admin_username = session.get('admin_username')
        super(ReposController, self).__before__()
                
    def index(self, format='html'):
        """GET /repos: All items in the collection"""
        # url('repos')
        c.repos_list = c.cached_repo_list
        return render('admin/repos/repos.html')
    
    def create(self):
        """POST /repos: Create a new item"""
        # url('repos')
        name = request.POST.get('name')

        try:
            self._create_repo(name)
            #clear our cached list for refresh with new repo
            invalidate_cache('cached_repo_list')
        except Exception as e:
            log.error(e)
        
        return redirect('repos')
        
    def _create_repo(self, repo_name):        
        repo_path = os.path.join(g.base_path, repo_name)
        if check_repo(repo_name, g.base_path):
            log.info('creating repo %s in %s', repo_name, repo_path)
            from vcs.backends.hg import MercurialRepository
            MercurialRepository(repo_path, create=True)
                        

    def new(self, format='html'):
        """GET /repos/new: Form to create a new item"""
        new_repo = request.GET.get('repo', '')
        c.new_repo = clean_repo(new_repo)

        return render('admin/repos/repo_add.html')

    def update(self, id):
        """PUT /repos/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('repo', id=ID),
        #           method='put')
        # url('repo', id=ID)

    def delete(self, id):
        """DELETE /repos/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('repo', id=ID),
        #           method='delete')
        # url('repo', id=ID)
        from datetime import datetime
        path = g.paths[0][1].replace('*', '')
        rm_path = os.path.join(path, id)
        log.info("Removing %s", rm_path)
        shutil.move(os.path.join(rm_path, '.hg'), os.path.join(rm_path, 'rm__.hg'))
        shutil.move(rm_path, os.path.join(path, 'rm__%s-%s' % (datetime.today(), id)))
        
        #clear our cached list for refresh with new repo
        invalidate_cache('cached_repo_list')
                    
        return redirect(url('repos'))
        

    def show(self, id, format='html'):
        """GET /repos/id: Show a specific item"""
        # url('repo', id=ID)
        return render('/repos_show.html')
    def edit(self, id, format='html'):
        """GET /repos/id/edit: Form to edit an existing item"""
        # url('edit_repo', id=ID)
