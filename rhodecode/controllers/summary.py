# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.summary
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Summary controller for Rhodecode
    
    :created_on: Apr 18, 2010
    :author: marcink
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>    
    :license: GPLv3, see COPYING for more details.
"""
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

import calendar
import logging
from time import mktime
from datetime import datetime, timedelta, date

from vcs.exceptions import ChangesetError

from pylons import tmpl_context as c, request, url
from pylons.i18n.translation import _

from rhodecode.model.db import Statistics

from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.utils import OrderedDict, EmptyChangeset

from rhodecode.lib.celerylib import run_task
from rhodecode.lib.celerylib.tasks import get_commits_stats
from rhodecode.lib.helpers import RepoPage

try:
    import json
except ImportError:
    #python 2.5 compatibility
    import simplejson as json
log = logging.getLogger(__name__)

class SummaryController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(SummaryController, self).__before__()

    def index(self):
        c.repo, dbrepo = self.scm_model.get(c.repo_name)
        c.dbrepo = dbrepo

        c.following = self.scm_model.is_following_repo(c.repo_name,
                                             self.rhodecode_user.user_id)
        def url_generator(**kw):
            return url('shortlog_home', repo_name=c.repo_name, **kw)

        c.repo_changesets = RepoPage(c.repo, page=1, items_per_page=10,
                                 url=url_generator)

        e = request.environ

        if self.rhodecode_user.username == 'default':
            #for default(anonymous) user we don't need to pass credentials
            username = ''
            password = ''
        else:
            username = str(self.rhodecode_user.username)
            password = '@'

        uri = u'%(protocol)s://%(user)s%(password)s%(host)s%(prefix)s/%(repo_name)s' % {
                                        'protocol': e.get('wsgi.url_scheme'),
                                        'user':username,
                                        'password':password,
                                        'host':e.get('HTTP_HOST'),
                                        'prefix':e.get('SCRIPT_NAME'),
                                        'repo_name':c.repo_name, }
        c.clone_repo_url = uri
        c.repo_tags = OrderedDict()
        for name, hash in c.repo.tags.items()[:10]:
            try:
                c.repo_tags[name] = c.repo.get_changeset(hash)
            except ChangesetError:
                c.repo_tags[name] = EmptyChangeset(hash)

        c.repo_branches = OrderedDict()
        for name, hash in c.repo.branches.items()[:10]:
            try:
                c.repo_branches[name] = c.repo.get_changeset(hash)
            except ChangesetError:
                c.repo_branches[name] = EmptyChangeset(hash)

        td = date.today() + timedelta(days=1)
        td_1m = td - timedelta(days=calendar.mdays[td.month])
        td_1y = td - timedelta(days=365)

        ts_min_m = mktime(td_1m.timetuple())
        ts_min_y = mktime(td_1y.timetuple())
        ts_max_y = mktime(td.timetuple())

        if dbrepo.enable_statistics:
            c.no_data_msg = _('No data loaded yet')
            run_task(get_commits_stats, c.repo.name, ts_min_y, ts_max_y)
        else:
            c.no_data_msg = _('Statistics are disabled for this repository')
        c.ts_min = ts_min_m
        c.ts_max = ts_max_y

        stats = self.sa.query(Statistics)\
            .filter(Statistics.repository == dbrepo)\
            .scalar()


        if stats and stats.languages:
            c.no_data = False is dbrepo.enable_statistics
            lang_stats = json.loads(stats.languages)
            c.commit_data = stats.commit_activity
            c.overview_data = stats.commit_activity_combined
            c.trending_languages = json.dumps(OrderedDict(
                                       sorted(lang_stats.items(), reverse=True,
                                            key=lambda k: k[1])[:10]
                                        )
                                    )
        else:
            c.commit_data = json.dumps({})
            c.overview_data = json.dumps([[ts_min_y, 0], [ts_max_y, 10] ])
            c.trending_languages = json.dumps({})
            c.no_data = True

        c.enable_downloads = dbrepo.enable_downloads
        if c.enable_downloads:
            c.download_options = self._get_download_links(c.repo)

        return render('summary/summary.html')



    def _get_download_links(self, repo):

        download_l = []

        branches_group = ([], _("Branches"))
        tags_group = ([], _("Tags"))

        for name, chs in c.rhodecode_repo.branches.items():
            #chs = chs.split(':')[-1]
            branches_group[0].append((chs, name),)
        download_l.append(branches_group)

        for name, chs in c.rhodecode_repo.tags.items():
            #chs = chs.split(':')[-1]
            tags_group[0].append((chs, name),)
        download_l.append(tags_group)

        return download_l
