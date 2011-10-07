# -*- coding: utf-8 -*-
"""
    rhodecode.tests.test_crawer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test for crawling a project for memory usage
    This should be runned just as regular script together
    with a watch script that will show memory usage.
    
    watch -n1 ./rhodecode/tests/mem_watch

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

from os.path import join as jn


BASE_URI = 'http://127.0.0.1:5000/%s'
PROJECT = 'CPython'
PROJECT_PATH = jn('/', 'home', 'marcink', 'hg_repos')


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


def test_changeset_walk(limit=None):
    print 'processing', jn(PROJECT_PATH, PROJECT)
    total_time = 0

    repo = vcs.get_repo(jn(PROJECT_PATH, PROJECT))
    cnt = 0
    for i in repo:
        cnt += 1
        raw_cs = '/'.join((PROJECT, 'changeset', i.raw_id))
        if limit and limit == cnt:
            break

        full_uri = (BASE_URI % raw_cs)
        s = time.time()
        f = o.open(full_uri)
        size = len(f.read())
        e = time.time() - s
        total_time += e
        print '%s visited %s\%s size:%s req:%s ms' % (cnt, full_uri, i, size, e)

    print 'total_time', total_time
    print 'average on req', total_time / float(cnt)


def test_files_walk(limit=100):
    print 'processing', jn(PROJECT_PATH, PROJECT)
    total_time = 0

    repo = vcs.get_repo(jn(PROJECT_PATH, PROJECT))

    from rhodecode.lib.compat import OrderedSet

    paths_ = OrderedSet([''])
    try:
        tip = repo.get_changeset('tip')
        for topnode, dirs, files in tip.walk('/'):

            for dir in dirs:
                paths_.add(dir.path)
                for f in dir:
                    paths_.add(f.path)

            for f in files:
                paths_.add(f.path)

    except vcs.exception.RepositoryError, e:
        pass

    cnt = 0
    for f in paths_:
        cnt += 1
        if limit and limit == cnt:
            break

        file_path = '/'.join((PROJECT, 'files', 'tip', f))

        full_uri = (BASE_URI % file_path)
        s = time.time()
        f = o.open(full_uri)
        size = len(f.read())
        e = time.time() - s
        total_time += e
        print '%s visited %s size:%s req:%s ms' % (cnt, full_uri, size, e)

    print 'total_time', total_time
    print 'average on req', total_time / float(cnt)



test_changelog_walk(40)
time.sleep(2)
test_changeset_walk(limit=100)
time.sleep(2)
test_files_walk(100)
