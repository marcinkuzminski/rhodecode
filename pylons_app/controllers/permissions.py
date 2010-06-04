#!/usr/bin/env python
# encoding: utf-8
# permissions controller for pylons
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your opinion) any later version of the license.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.
"""
Created on April 27, 2010
permissions controller for pylons
@author: marcink
"""
import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from pylons_app.lib.base import BaseController, render

log = logging.getLogger(__name__)

class PermissionsController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('permission', 'permissions')

    def index(self, format='html'):
        """GET /permissions: All items in the collection"""
        # url('permissions')
        return render('admin/permissions/permissions.html')

    def create(self):
        """POST /permissions: Create a new item"""
        # url('permissions')

    def new(self, format='html'):
        """GET /permissions/new: Form to create a new item"""
        # url('new_permission')

    def update(self, id):
        """PUT /permissions/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('permission', id=ID),
        #           method='put')
        # url('permission', id=ID)

    def delete(self, id):
        """DELETE /permissions/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('permission', id=ID),
        #           method='delete')
        # url('permission', id=ID)

    def show(self, id, format='html'):
        """GET /permissions/id: Show a specific item"""
        # url('permission', id=ID)

    def edit(self, id, format='html'):
        """GET /permissions/id/edit: Form to edit an existing item"""
        # url('edit_permission', id=ID)
