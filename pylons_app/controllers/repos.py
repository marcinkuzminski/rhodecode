import logging
import os
from pylons import request, response, session, tmpl_context as c, url, app_globals as g
from pylons.controllers.util import abort, redirect
from pylons_app.lib import auth
from pylons_app.lib.base import BaseController, render
from pylons_app.model import meta
from pylons_app.model.db import Users, UserLogs
from pylons_app.lib.auth import authenticate
from pylons_app.model.hg_model import HgModel
from operator import itemgetter
import shutil
log = logging.getLogger(__name__)

class ReposController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('repo', 'repos')
    
    @authenticate
    def __before__(self):
        
        c.admin_user = session.get('admin_user')
        c.admin_username = session.get('admin_username')
        self.sa = meta.Session
                
    def index(self, format='html'):
        """GET /repos: All items in the collection"""
        # url('repos')
        hg_model = HgModel()
        c.repos_list = list(hg_model.get_repos())
        c.repos_list.sort(key=itemgetter('name'))
        return render('/repos.html')
    
    def create(self):
        """POST /repos: Create a new item"""
        # url('repos')

    def new(self, format='html'):
        """GET /repos/new: Form to create a new item"""
        # url('new_repo')

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
        return redirect(url('repos'))
        

    def show(self, id, format='html'):
        """GET /repos/id: Show a specific item"""
        # url('repo', id=ID)
        return render('/repos_show.html')
    def edit(self, id, format='html'):
        """GET /repos/id/edit: Form to edit an existing item"""
        # url('edit_repo', id=ID)
