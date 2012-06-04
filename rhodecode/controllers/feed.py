# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.feed
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Feed controller for rhodecode

    :created_on: Apr 23, 2010
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

from pylons import url, response, tmpl_context as c
from pylons.i18n.translation import _

from webhelpers.feedgenerator import Atom1Feed, Rss201rev2Feed

from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseRepoController
from rhodecode.lib.diffs import DiffProcessor

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
        self.feed_nr = 20

    def _get_title(self, cs):
        return "%s" % (
            h.shorter(cs.message, 160)
        )

    def __changes(self, cs):
        changes = []

        diffprocessor = DiffProcessor(cs.diff())
        stats = diffprocessor.prepare(inline_diff=False)
        for st in stats:
            st.update({'added': st['stats'][0],
                       'removed': st['stats'][1]})
            changes.append('\n %(operation)s %(filename)s '
                           '(%(added)s lines added, %(removed)s lines removed)'
                            % st)
        return changes

    def __get_desc(self, cs):
        desc_msg = []
        desc_msg.append('%s %s %s:<br/>' % (cs.author, _('commited on'),
                                           cs.date))
        desc_msg.append('<pre>')
        desc_msg.append(cs.message)
        desc_msg.append('\n')
        desc_msg.extend(self.__changes(cs))
        desc_msg.append('</pre>')
        return desc_msg

    def atom(self, repo_name):
        """Produce an atom-1.0 feed via feedgenerator module"""
        feed = Atom1Feed(
             title=self.title % repo_name,
             link=url('summary_home', repo_name=repo_name,
                      qualified=True),
             description=self.description % repo_name,
             language=self.language,
             ttl=self.ttl
        )

        for cs in reversed(list(c.rhodecode_repo[-self.feed_nr:])):
            feed.add_item(title=self._get_title(cs),
                          link=url('changeset_home', repo_name=repo_name,
                                   revision=cs.raw_id, qualified=True),
                          author_name=cs.author,
                          description=''.join(self.__get_desc(cs)),
                          pubdate=cs.date,
                          )

        response.content_type = feed.mime_type
        return feed.writeString('utf-8')

    def rss(self, repo_name):
        """Produce an rss2 feed via feedgenerator module"""
        feed = Rss201rev2Feed(
            title=self.title % repo_name,
            link=url('summary_home', repo_name=repo_name,
                     qualified=True),
            description=self.description % repo_name,
            language=self.language,
            ttl=self.ttl
        )

        for cs in reversed(list(c.rhodecode_repo[-self.feed_nr:])):
            feed.add_item(title=self._get_title(cs),
                          link=url('changeset_home', repo_name=repo_name,
                                   revision=cs.raw_id, qualified=True),
                          author_name=cs.author,
                          description=''.join(self.__get_desc(cs)),
                          pubdate=cs.date,
                         )

        response.content_type = feed.mime_type
        return feed.writeString('utf-8')
