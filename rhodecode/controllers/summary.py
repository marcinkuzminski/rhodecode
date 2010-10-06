#!/usr/bin/env python
# encoding: utf-8
# summary controller for pylons
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
# 
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
Created on April 18, 2010
summary controller for pylons
@author: marcink
"""
from pylons import tmpl_context as c, request, url
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.utils import OrderedDict
from rhodecode.model.hg_model import HgModel
from rhodecode.model.db import Statistics
from webhelpers.paginate import Page
from rhodecode.lib.celerylib import run_task
from rhodecode.lib.celerylib.tasks import get_commits_stats
from datetime import datetime, timedelta
from time import mktime
import calendar
import logging
import json
log = logging.getLogger(__name__)

class SummaryController(BaseController):
    
    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')           
    def __before__(self):
        super(SummaryController, self).__before__()
                
    def index(self):
        hg_model = HgModel()
        c.repo_info = hg_model.get_repo(c.repo_name)
        c.repo_changesets = Page(list(c.repo_info[:10]), page=1, items_per_page=20)
        e = request.environ
            
        uri = u'%(protocol)s://%(user)s@%(host)s%(prefix)s/%(repo_name)s' % {
                                        'protocol': e.get('wsgi.url_scheme'),
                                        'user':str(c.hg_app_user.username),
                                        'host':e.get('HTTP_HOST'),
                                        'prefix':e.get('SCRIPT_NAME'),
                                        'repo_name':c.repo_name, }
        c.clone_repo_url = uri
        c.repo_tags = OrderedDict()
        for name, hash in c.repo_info.tags.items()[:10]:
            c.repo_tags[name] = c.repo_info.get_changeset(hash)
        
        c.repo_branches = OrderedDict()
        for name, hash in c.repo_info.branches.items()[:10]:
            c.repo_branches[name] = c.repo_info.get_changeset(hash)
        
        td = datetime.today() + timedelta(days=1) 
        y, m, d = td.year, td.month, td.day
        
        ts_min_y = mktime((y - 1, (td - timedelta(days=calendar.mdays[m])).month,
                            d, 0, 0, 0, 0, 0, 0,))
        ts_min_m = mktime((y, (td - timedelta(days=calendar.mdays[m])).month,
                            d, 0, 0, 0, 0, 0, 0,))
        
        ts_max_y = mktime((y, m, d, 0, 0, 0, 0, 0, 0,))
            
        run_task(get_commits_stats, c.repo_info.name, ts_min_y, ts_max_y)
        c.ts_min = ts_min_m
        c.ts_max = ts_max_y
        
        stats = self.sa.query(Statistics)\
            .filter(Statistics.repository == c.repo_info.dbrepo)\
            .scalar()
        
        
        if stats and stats.languages:
            lang_stats = json.loads(stats.languages)
            c.commit_data = stats.commit_activity
            c.overview_data = stats.commit_activity_combined
            c.trending_languages = json.dumps(OrderedDict(
                                       sorted(lang_stats.items(), reverse=True,
                                            key=lambda k: k[1])[:2]
                                        )
                                    )
        else:
            c.commit_data = json.dumps({})
            c.overview_data = json.dumps([[ts_min_y, 0], [ts_max_y, 0] ])
            c.trending_languages = json.dumps({})
        
        return render('summary/summary.html')

