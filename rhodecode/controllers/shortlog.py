# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.shortlog
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Shortlog controller for rhodecode

    :created_on: Apr 18, 2010
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

from pylons import tmpl_context as c, request, url
from pylons.i18n.translation import _

from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.helpers import RepoPage
from pylons.controllers.util import redirect
from rhodecode.lib.utils2 import safe_int
from rhodecode.lib.vcs.exceptions import NodeDoesNotExistError, ChangesetError,\
    RepositoryError

log = logging.getLogger(__name__)


class ShortlogController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(ShortlogController, self).__before__()

    def __get_cs_or_redirect(self, rev, repo_name, redirect_after=True):
        """
        Safe way to get changeset if error occur it redirects to tip with
        proper message

        :param rev: revision to fetch
        :param repo_name: repo name to redirect after
        """

        try:
            return c.rhodecode_repo.get_changeset(rev)
        except RepositoryError, e:
            h.flash(str(e), category='warning')
            redirect(h.url('shortlog_home', repo_name=repo_name))

    def index(self, repo_name, revision=None, f_path=None):
        p = safe_int(request.params.get('page', 1), 1)
        size = safe_int(request.params.get('size', 20), 20)
        collection = c.rhodecode_repo
        c.file_history = f_path

        def url_generator(**kw):
            if f_path:
                return url('shortlog_file_home', repo_name=repo_name,
                           revision=revision, f_path=f_path, size=size, **kw)
            return url('shortlog_home', repo_name=repo_name, size=size, **kw)

        if f_path:
            log.debug('generating shortlog for path %s' % f_path)
            # get the history for the file !
            tip_cs = c.rhodecode_repo.get_changeset()
            try:
                collection = tip_cs.get_file_history(f_path)
            except (NodeDoesNotExistError, ChangesetError):
                #this node is not present at tip !
                try:
                    cs = self.__get_cs_or_redirect(revision, repo_name)
                    collection = cs.get_file_history(f_path)
                except RepositoryError, e:
                    h.flash(str(e), category='warning')
                    redirect(h.url('shortlog_home', repo_name=repo_name))
            collection = list(reversed(collection))

        c.repo_changesets = RepoPage(collection, page=p,
                                     items_per_page=size, url=url_generator)
        page_revisions = [x.raw_id for x in list(c.repo_changesets)]
        c.statuses = c.rhodecode_db_repo.statuses(page_revisions)

        if not c.repo_changesets:
            h.flash(_('There are no changesets yet'), category='warning')
            return redirect(url('summary_home', repo_name=repo_name))

        c.shortlog_data = render('shortlog/shortlog_data.html')
        if request.environ.get('HTTP_X_PARTIAL_XHR'):
            return c.shortlog_data
        r = render('shortlog/shortlog.html')
        return r
