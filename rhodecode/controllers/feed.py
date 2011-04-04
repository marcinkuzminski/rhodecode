# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.feed
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Feed controller for rhodecode

    :created_on: Apr 23, 2010
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

import logging

from pylons import url, response, tmpl_context as c
from pylons.i18n.translation import _

from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseRepoController

from webhelpers.feedgenerator import Atom1Feed, Rss201rev2Feed

log = logging.getLogger(__name__)

class FeedController(BaseRepoController):

    @LoginRequired(api_access=True)
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(FeedController, self).__before__()
        #common values for feeds
        self.description = _('Changes on %s repository')
        self.title = self.title = _('%s %s feed') % (c.rhodecode_name, '%s')
        self.language = 'en-us'
        self.ttl = "5"
        self.feed_nr = 10

    def __changes(self, cs):
        changes = ''

        a = [n.path for n in cs.added]
        if a:
            changes += '\nA ' + '\nA '.join(a)

        m = [n.path for n in cs.changed]
        if m:
            changes += '\nM ' + '\nM '.join(m)

        d = [n.path for n in cs.removed]
        if d:
            changes += '\nD ' + '\nD '.join(d)

        changes += '</pre>'

        return changes

    def atom(self, repo_name):
        """Produce an atom-1.0 feed via feedgenerator module"""
        feed = Atom1Feed(title=self.title % repo_name,
                         link=url('summary_home', repo_name=repo_name, qualified=True),
                         description=self.description % repo_name,
                         language=self.language,
                         ttl=self.ttl)

        for cs in reversed(list(c.rhodecode_repo[-self.feed_nr:])):
            desc = '%s - %s<br/><pre>' % (cs.author, cs.date)
            desc += self.__changes(cs)

            feed.add_item(title=cs.message,
                          link=url('changeset_home', repo_name=repo_name,
                                   revision=cs.raw_id, qualified=True),
                          author_name=cs.author,
                          description=desc)

        response.content_type = feed.mime_type
        return feed.writeString('utf-8')


    def rss(self, repo_name):
        """Produce an rss2 feed via feedgenerator module"""
        feed = Rss201rev2Feed(title=self.title % repo_name,
                         link=url('summary_home', repo_name=repo_name, qualified=True),
                         description=self.description % repo_name,
                         language=self.language,
                         ttl=self.ttl)

        for cs in reversed(list(c.rhodecode_repo[-self.feed_nr:])):
            desc = '%s - %s<br/><pre>' % (cs.author, cs.date)
            desc += self.__changes(cs)

            feed.add_item(title=cs.message,
                          link=url('changeset_home', repo_name=repo_name,
                                   revision=cs.raw_id, qualified=True),
                          author_name=cs.author,
                          description=desc,
                         )

        response.content_type = feed.mime_type
        return feed.writeString('utf-8')
