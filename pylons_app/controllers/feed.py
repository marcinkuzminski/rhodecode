#!/usr/bin/python
# -*- coding: utf-8 -*-
from pylons import tmpl_context as c, url, response
from pylons_app.lib.base import BaseController, render
from pylons_app.model.hg_model import _full_changelog_cached
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
        
        
        for cnt, cs in enumerate(_full_changelog_cached(repo_name)):
            if cnt > self.feed_nr:
                break
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
        
        for cnt, cs in enumerate(_full_changelog_cached(repo_name)):
            if cnt > self.feed_nr:
                break
            feed.add_item(title=cs.message,
                          link=url('changeset_home', repo_name=repo_name, revision=cs.raw_id, qualified=True),
                          description=str(cs.date))
            
        response.content_type = feed.mime_type
        return feed.writeString('utf-8')
