import logging
from operator import itemgetter

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from rhodecode.lib.base import BaseController, render
from rhodecode.model.db import Group

log = logging.getLogger(__name__)

class ReposGroupsController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('repos_group', 'repos_groups')

    def index(self, format='html'):
        """GET /repos_groups: All items in the collection"""
        # url('repos_groups')

    def create(self):
        """POST /repos_groups: Create a new item"""
        # url('repos_groups')

    def new(self, format='html'):
        """GET /repos_groups/new: Form to create a new item"""
        # url('new_repos_group')

    def update(self, id):
        """PUT /repos_groups/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('repos_group', id=ID),
        #           method='put')
        # url('repos_group', id=ID)

    def delete(self, id):
        """DELETE /repos_groups/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('repos_group', id=ID),
        #           method='delete')
        # url('repos_group', id=ID)

    def show(self, id, format='html'):
        """GET /repos_groups/id: Show a specific item"""
        # url('repos_group', id=ID)

        c.group = Group.get(id)
        if c.group:
            c.group_repos = c.group.repositories
        else:
            return redirect(url('repos_group'))

        sortables = ['name', 'description', 'last_change', 'tip', 'owner']
        current_sort = request.GET.get('sort', 'name')
        current_sort_slug = current_sort.replace('-', '')

        if current_sort_slug not in sortables:
            c.sort_by = 'name'
            current_sort_slug = c.sort_by
        else:
            c.sort_by = current_sort
        c.sort_slug = current_sort_slug

        sort_key = current_sort_slug + '_sort'


        #overwrite our cached list with current filter
        gr_filter = [r.repo_name for r in c.group_repos]
        c.cached_repo_list = self.scm_model.get_repos(all_repos=gr_filter)

        if c.sort_by.startswith('-'):
            c.repos_list = sorted(c.cached_repo_list, key=itemgetter(sort_key),
                                  reverse=True)
        else:
            c.repos_list = sorted(c.cached_repo_list, key=itemgetter(sort_key),
                                  reverse=False)

        c.repo_cnt = len(c.repos_list)


        return render('admin/repos_groups/repos_groups.html')


    def edit(self, id, format='html'):
        """GET /repos_groups/id/edit: Form to edit an existing item"""
        # url('edit_repos_group', id=ID)
