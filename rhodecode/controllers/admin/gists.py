# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.admin.gist
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    gist controller for RhodeCode

    :created_on: May 9, 2013
    :author: marcink
    :copyright: (C) 2010-2013 Marcin Kuzminski <marcin@python-works.com>
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
import time
import logging
import traceback
import formencode
from formencode import htmlfill

from pylons import request, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _

from rhodecode.model.forms import GistForm
from rhodecode.model.gist import GistModel
from rhodecode.model.meta import Session
from rhodecode.model.db import Gist
from rhodecode.lib import helpers as h
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.auth import LoginRequired, NotAnonymous
from rhodecode.lib.utils2 import safe_str, safe_int, time_to_datetime
from rhodecode.lib.helpers import Page
from webob.exc import HTTPNotFound, HTTPForbidden
from sqlalchemy.sql.expression import or_
from rhodecode.lib.vcs.exceptions import VCSError

log = logging.getLogger(__name__)


class GistsController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""

    def __load_defaults(self):
        c.lifetime_values = [
            (str(-1), _('forever')),
            (str(5), _('5 minutes')),
            (str(60), _('1 hour')),
            (str(60 * 24), _('1 day')),
            (str(60 * 24 * 30), _('1 month')),
        ]
        c.lifetime_options = [(c.lifetime_values, _("Lifetime"))]

    @LoginRequired()
    def index(self, format='html'):
        """GET /admin/gists: All items in the collection"""
        # url('gists')
        c.show_private = request.GET.get('private') and c.rhodecode_user.username != 'default'
        c.show_public = request.GET.get('public') and c.rhodecode_user.username != 'default'

        gists = Gist().query()\
            .filter(or_(Gist.gist_expires == -1, Gist.gist_expires >= time.time()))\
            .order_by(Gist.created_on.desc())
        if c.show_private:
            c.gists = gists.filter(Gist.gist_type == Gist.GIST_PRIVATE)\
                             .filter(Gist.gist_owner == c.rhodecode_user.user_id)
        elif c.show_public:
            c.gists = gists.filter(Gist.gist_type == Gist.GIST_PUBLIC)\
                             .filter(Gist.gist_owner == c.rhodecode_user.user_id)

        else:
            c.gists = gists.filter(Gist.gist_type == Gist.GIST_PUBLIC)
        p = safe_int(request.GET.get('page', 1), 1)
        c.gists_pager = Page(c.gists, page=p, items_per_page=10)
        return render('admin/gists/index.html')

    @LoginRequired()
    @NotAnonymous()
    def create(self):
        """POST /admin/gists: Create a new item"""
        # url('gists')
        self.__load_defaults()
        gist_form = GistForm([x[0] for x in c.lifetime_values])()
        try:
            form_result = gist_form.to_python(dict(request.POST))
            #TODO: multiple files support, from the form
            nodes = {
                form_result['filename'] or 'gistfile1.txt': {
                    'content': form_result['content'],
                    'lexer': None  # autodetect
                }
            }
            _public = form_result['public']
            gist_type = Gist.GIST_PUBLIC if _public else Gist.GIST_PRIVATE
            gist = GistModel().create(
                description=form_result['description'],
                owner=c.rhodecode_user,
                gist_mapping=nodes,
                gist_type=gist_type,
                lifetime=form_result['lifetime']
            )
            Session().commit()
            new_gist_id = gist.gist_access_id
        except formencode.Invalid, errors:
            defaults = errors.value

            return formencode.htmlfill.render(
                render('admin/gists/new.html'),
                defaults=defaults,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8"
            )

        except Exception, e:
            log.error(traceback.format_exc())
            h.flash(_('Error occurred during gist creation'), category='error')
            return redirect(url('new_gist'))
        return redirect(url('gist', id=new_gist_id))

    @LoginRequired()
    @NotAnonymous()
    def new(self, format='html'):
        """GET /admin/gists/new: Form to create a new item"""
        # url('new_gist')
        self.__load_defaults()
        return render('admin/gists/new.html')

    @LoginRequired()
    @NotAnonymous()
    def update(self, id):
        """PUT /admin/gists/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('gist', id=ID),
        #           method='put')
        # url('gist', id=ID)

    @LoginRequired()
    @NotAnonymous()
    def delete(self, id):
        """DELETE /admin/gists/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('gist', id=ID),
        #           method='delete')
        # url('gist', id=ID)
        gist = GistModel().get_gist(id)
        owner = gist.gist_owner == c.rhodecode_user.user_id
        if h.HasPermissionAny('hg.admin')() or owner:
            GistModel().delete(gist)
            Session().commit()
            h.flash(_('Deleted gist %s') % gist.gist_access_id, category='success')
        else:
            raise HTTPForbidden()

        return redirect(url('gists'))

    @LoginRequired()
    def show(self, id, format='html'):
        """GET /admin/gists/id: Show a specific item"""
        # url('gist', id=ID)
        gist_id = id
        c.gist = Gist.get_or_404(gist_id)

        #check if this gist is not expired
        if c.gist.gist_expires != -1:
            if time.time() > c.gist.gist_expires:
                log.error('Gist expired at %s' %
                          (time_to_datetime(c.gist.gist_expires)))
                raise HTTPNotFound()
        try:
            c.file_changeset, c.files = GistModel().get_gist_files(gist_id)
        except VCSError:
            log.error(traceback.format_exc())
            raise HTTPNotFound()

        return render('admin/gists/show.html')

    @LoginRequired()
    @NotAnonymous()
    def edit(self, id, format='html'):
        """GET /admin/gists/id/edit: Form to edit an existing item"""
        # url('edit_gist', id=ID)
