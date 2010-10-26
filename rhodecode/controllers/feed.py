#!/usr/bin/env python
# encoding: utf-8
# feed controller for pylons
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
Created on April 23, 2010
feed controller for pylons
@author: marcink
"""
from pylons import tmpl_context as c, url, response
from rhodecode.lib.base import BaseController, render
from rhodecode.model.hg import HgModel
from webhelpers.feedgenerator import Atom1Feed, Rss201rev2Feed
import logging
log = logging.getLogger(__name__)

class FeedController(BaseController):
    
    #secure it or not ?
    def __before__(self):
        super(FeedController, self).__before__()
        #common values for feeds
        self.description = 'Changes on %s repository'
        self.title = "%s feed"
        self.language = 'en-us'
        self.ttl = "5"
        self.feed_nr = 10

    def atom(self, repo_name):
        """Produce an atom-1.0 feed via feedgenerator module"""
        feed = Atom1Feed(title=self.title % repo_name,
                         link=url('summary_home', repo_name=repo_name, qualified=True),
                         description=self.description % repo_name,
                         language=self.language,
                         ttl=self.ttl)
        
        changesets = HgModel().get_repo(repo_name)

        for cs in changesets[:self.feed_nr]:
            feed.add_item(title=cs.message,
                          link=url('changeset_home', repo_name=repo_name,
                                   revision=cs.raw_id, qualified=True),
                                   description=str(cs.date))
        
        response.content_type = feed.mime_type
        return feed.writeString('utf-8')

    
    def rss(self, repo_name):
        """Produce an rss2 feed via feedgenerator module"""
        feed = Rss201rev2Feed(title=self.title % repo_name,
                         link=url('summary_home', repo_name=repo_name, qualified=True),
                         description=self.description % repo_name,
                         language=self.language,
                         ttl=self.ttl)
        
        changesets = HgModel().get_repo(repo_name)
        for cs in changesets[:self.feed_nr]:
            feed.add_item(title=cs.message,
                          link=url('changeset_home', repo_name=repo_name,
                                   revision=cs.raw_id, qualified=True),
                          description=str(cs.date))
            
        response.content_type = feed.mime_type
        return feed.writeString('utf-8')
