import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from rhodecode.lib.base import BaseController, render

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

    def edit(self, id, format='html'):
        """GET /repos_groups/id/edit: Form to edit an existing item"""
        # url('edit_repos_group', id=ID)
