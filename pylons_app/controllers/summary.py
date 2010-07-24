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
from datetime import datetime, timedelta
from pylons import tmpl_context as c, request
from pylons_app.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from pylons_app.lib.base import BaseController, render
from pylons_app.lib.helpers import person
from pylons_app.lib.utils import OrderedDict
from pylons_app.model.hg_model import HgModel
from time import mktime
from webhelpers.paginate import Page
import calendar
import logging

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
        uri = u'%(protocol)s://%(user)s@%(host)s/%(repo_name)s' % {
                                        'protocol': e.get('wsgi.url_scheme'),
                                        'user':str(c.hg_app_user.username),
                                        'host':e.get('HTTP_HOST'),
                                        'repo_name':c.repo_name, }
        c.clone_repo_url = uri
        c.repo_tags = {}
        for name, hash in c.repo_info.tags.items()[:10]:
            c.repo_tags[name] = c.repo_info.get_changeset(hash)
        
        c.repo_branches = {}
        for name, hash in c.repo_info.branches.items()[:10]:
            c.repo_branches[name] = c.repo_info.get_changeset(hash)

        c.commit_data = self.__get_commit_stats(c.repo_info)
        
        return render('summary/summary.html')



    def __get_commit_stats(self, repo):
        aggregate = OrderedDict()
        
        
        #graph range
        td = datetime.today() 
        y = td.year
        m = td.month
        d = td.day
        c.ts_min = mktime((y, (td - timedelta(days=calendar.mdays[m] - 1)).month, d, 0, 0, 0, 0, 0, 0,))
        c.ts_max = mktime((y, m, d, 0, 0, 0, 0, 0, 0,))
        
        
#        #generate this monhts keys
#        dates_range = OrderedDict()
#        year_range = range(2010, datetime.today().year + 1)
#        month_range = range(1, datetime.today().month + 1)
#        
#
#        
#        for y in year_range:
#            for m in month_range:
#                for d in range(1, calendar.mdays[m] + 1):
#                    k = '%s-%s-%s' % (y, m, d)
#                    timetupple = [int(x) for x in k.split('-')]
#                    timetupple.extend([0 for _ in xrange(6)])
#                    k = mktime(timetupple)                    
#                    dates_range[k] = 0
        
        def author_key_cleaner(k):
            k = person(k)
            return k
                
        for cs in repo:
            k = '%s-%s-%s' % (cs.date.timetuple()[0], cs.date.timetuple()[1],
                              cs.date.timetuple()[2])
            timetupple = [int(x) for x in k.split('-')]
            timetupple.extend([0 for _ in xrange(6)])
            k = mktime(timetupple)
            if aggregate.has_key(author_key_cleaner(cs.author)):
                if aggregate[author_key_cleaner(cs.author)].has_key(k):
                    aggregate[author_key_cleaner(cs.author)][k] += 1
                else:
                    #aggregate[author_key_cleaner(cs.author)].update(dates_range)
                    if k >= c.ts_min and k <= c.ts_max:
                        aggregate[author_key_cleaner(cs.author)][k] = 1
            else:
                if k >= c.ts_min and k <= c.ts_max:
                    aggregate[author_key_cleaner(cs.author)] = OrderedDict()
                    #aggregate[author_key_cleaner(cs.author)].update(dates_range)
                    aggregate[author_key_cleaner(cs.author)][k] = 1
        
        d = ''
        tmpl0 = u""""%s":%s"""
        tmpl1 = u"""{label:"%s",data:%s},"""
        for author in aggregate:
            d += tmpl0 % (author.decode('utf8'),
                          tmpl1 \
                          % (author.decode('utf8'),
                        [[x, aggregate[author][x]] for x in aggregate[author]]))
        if d == '':
            d = '"%s":{label:"%s",data:[[0,0],]}' \
                % (author_key_cleaner(repo.contact),
                   author_key_cleaner(repo.contact))
        return d


