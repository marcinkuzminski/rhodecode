# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.admin.defaults
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    default settings controller for Rhodecode

    :created_on: Apr 27, 2010
    :author: marcink
    :copyright: (C) 2010-2012 Marcin Kuzminski <marcin@python-works.com>
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import traceback
import formencode
from formencode import htmlfill

from pylons import request, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _

from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator
from rhodecode.lib.base import BaseController, render
from rhodecode.model.forms import DefaultsForm
from rhodecode.model.meta import Session
from rhodecode import BACKENDS
from rhodecode.model.db import RhodeCodeSetting

log = logging.getLogger(__name__)


class DefaultsController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('default', 'defaults')

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def __before__(self):
        super(DefaultsController, self).__before__()

    def index(self, format='html'):
        """GET /defaults: All items in the collection"""
        # url('defaults')
        c.backends = BACKENDS.keys()
        defaults = RhodeCodeSetting.get_default_repo_settings()

        return htmlfill.render(
            render('admin/defaults/defaults.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )

    def create(self):
        """POST /defaults: Create a new item"""
        # url('defaults')

    def new(self, format='html'):
        """GET /defaults/new: Form to create a new item"""
        # url('new_default')

    def update(self, id):
        """PUT /defaults/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('default', id=ID),
        #           method='put')
        # url('default', id=ID)

        _form = DefaultsForm()()

        try:
            form_result = _form.to_python(dict(request.POST))
            for k, v in form_result.iteritems():
                setting = RhodeCodeSetting.get_by_name_or_create(k)
                setting.app_settings_value = v
                Session().add(setting)
            Session().commit()
            h.flash(_('Default settings updated successfully'),
                    category='success')

        except formencode.Invalid, errors:
            defaults = errors.value

            return htmlfill.render(
                render('admin/defaults/defaults.html'),
                defaults=defaults,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('Error occurred during update of defaults'),
                    category='error')

        return redirect(url('defaults'))

    def delete(self, id):
        """DELETE /defaults/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('default', id=ID),
        #           method='delete')
        # url('default', id=ID)

    def show(self, id, format='html'):
        """GET /defaults/id: Show a specific item"""
        # url('default', id=ID)

    def edit(self, id, format='html'):
        """GET /defaults/id/edit: Form to edit an existing item"""
        # url('edit_default', id=ID)
