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

import calendar
import logging
from time import mktime
from datetime import datetime, timedelta, date

from vcs.exceptions import ChangesetError

from pylons import tmpl_context as c, request, url
from pylons.i18n.translation import _

from rhodecode.model.db import Statistics, Repository
from rhodecode.model.repo import RepoModel

from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.utils import EmptyChangeset

from rhodecode.lib.celerylib import run_task
from rhodecode.lib.celerylib.tasks import get_commits_stats, \
    LANGUAGES_EXTENSIONS_MAP
from rhodecode.lib.helpers import RepoPage
from rhodecode.lib.compat import json, OrderedDict

log = logging.getLogger(__name__)


class SummaryController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(SummaryController, self).__before__()

    def index(self, repo_name):

        e = request.environ
        c.dbrepo = dbrepo = c.rhodecode_db_repo

        c.following = self.scm_model.is_following_repo(repo_name,
                                                self.rhodecode_user.user_id)

        def url_generator(**kw):
            return url('shortlog_home', repo_name=repo_name, size=10, **kw)

        c.repo_changesets = RepoPage(c.rhodecode_repo, page=1,
                                     items_per_page=10, url=url_generator)

        if self.rhodecode_user.username == 'default':
            #for default(anonymous) user we don't need to pass credentials
            username = ''
            password = ''
        else:
            username = str(self.rhodecode_user.username)
            password = '@'

        if e.get('wsgi.url_scheme') == 'https':
            split_s = 'https://'
        else:
            split_s = 'http://'

        qualified_uri = [split_s] + [url.current(qualified=True)\
                                     .split(split_s)[-1]]
        uri = u'%(proto)s%(user)s%(pass)s%(rest)s' \
                % {'user': username,
                     'pass': password,
                     'proto': qualified_uri[0],
                     'rest': qualified_uri[1]}
        c.clone_repo_url = uri
        c.repo_tags = OrderedDict()
        for name, hash in c.rhodecode_repo.tags.items()[:10]:
            try:
                c.repo_tags[name] = c.rhodecode_repo.get_changeset(hash)
            except ChangesetError:
                c.repo_tags[name] = EmptyChangeset(hash)

        c.repo_branches = OrderedDict()
        for name, hash in c.rhodecode_repo.branches.items()[:10]:
            try:
                c.repo_branches[name] = c.rhodecode_repo.get_changeset(hash)
            except ChangesetError:
                c.repo_branches[name] = EmptyChangeset(hash)

        td = date.today() + timedelta(days=1)
        td_1m = td - timedelta(days=calendar.mdays[td.month])
        td_1y = td - timedelta(days=365)

        ts_min_m = mktime(td_1m.timetuple())
        ts_min_y = mktime(td_1y.timetuple())
        ts_max_y = mktime(td.timetuple())

        if dbrepo.enable_statistics:
            c.show_stats = True
            c.no_data_msg = _('No data loaded yet')
            run_task(get_commits_stats, c.dbrepo.repo_name, ts_min_y, ts_max_y)
        else:
            c.show_stats = False
            c.no_data_msg = _('Statistics are disabled for this repository')
        c.ts_min = ts_min_m
        c.ts_max = ts_max_y

        stats = self.sa.query(Statistics)\
            .filter(Statistics.repository == dbrepo)\
            .scalar()

        c.stats_percentage = 0

        if stats and stats.languages:
            c.no_data = False is dbrepo.enable_statistics
            lang_stats_d = json.loads(stats.languages)
            c.commit_data = stats.commit_activity
            c.overview_data = stats.commit_activity_combined

            lang_stats = ((x, {"count": y,
                               "desc": LANGUAGES_EXTENSIONS_MAP.get(x)})
                          for x, y in lang_stats_d.items())

            c.trending_languages = json.dumps(
                sorted(lang_stats, reverse=True, key=lambda k: k[1])[:10]
            )
            last_rev = stats.stat_on_revision + 1
            c.repo_last_rev = c.rhodecode_repo.count()\
                if c.rhodecode_repo.revisions else 0
            if last_rev == 0 or c.repo_last_rev == 0:
                pass
            else:
                c.stats_percentage = '%.2f' % ((float((last_rev)) /
                                                c.repo_last_rev) * 100)
        else:
            c.commit_data = json.dumps({})
            c.overview_data = json.dumps([[ts_min_y, 0], [ts_max_y, 10]])
            c.trending_languages = json.dumps({})
            c.no_data = True

        c.enable_downloads = dbrepo.enable_downloads
        if c.enable_downloads:
            c.download_options = self._get_download_links(c.rhodecode_repo)

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
