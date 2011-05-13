# -*- coding: utf-8 -*-
"""
    rhodecode.tests.test_crawer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test for crawling a project for memory usage
    
    watch -n 1 "ps aux |grep paster"

    :created_on: Apr 21, 2010
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


import cookielib
import urllib
import urllib2
import vcs
import time

BASE_URI = 'http://127.0.0.1:5000/%s'
PROJECT = 'rhodecode'


cj = cookielib.FileCookieJar('/tmp/rc_test_cookie.txt')
o = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
o.addheaders = [
                     ('User-agent', 'rhodecode-crawler'),
                     ('Accept-Language', 'en - us, en;q = 0.5')
                    ]

urllib2.install_opener(o)



def test_changelog_walk(pages=100):
    total_time = 0
    for i in range(1, pages):

        page = '/'.join((PROJECT, 'changelog',))

        full_uri = (BASE_URI % page) + '?' + urllib.urlencode({'page':i})
        s = time.time()
        f = o.open(full_uri)
        size = len(f.read())
        e = time.time() - s
        total_time += e
        print 'visited %s size:%s req:%s ms' % (full_uri, size, e)


    print 'total_time', total_time
    print 'average on req', total_time / float(pages)


def test_changeset_walk():

    # test against self
    repo = vcs.get_repo('../../../rhodecode')

    total_time = 0
    for i in repo:

        raw_cs = '/'.join((PROJECT, 'changeset', i.raw_id))

        full_uri = (BASE_URI % raw_cs)
        s = time.time()
        f = o.open(full_uri)
        size = len(f.read())
        e = time.time() - s
        total_time += e
        print 'visited %s\%s size:%s req:%s ms' % (full_uri, i, size, e)

    print 'total_time', total_time
    print 'average on req', total_time / float(len(repo))

def test_files_walk():
    pass



test_changelog_walk()
#test_changeset_walk()
