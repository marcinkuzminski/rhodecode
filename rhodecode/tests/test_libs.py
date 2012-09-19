# -*- coding: utf-8 -*-
"""
    rhodecode.tests.test_libs
    ~~~~~~~~~~~~~~~~~~~~~~~~~


    Package for testing various lib/helper functions in rhodecode

    :created_on: Jun 9, 2011
    :copyright: (C) 2011-2012 Marcin Kuzminski <marcin@python-works.com>
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
from __future__ import with_statement
import unittest
import datetime
import hashlib
import mock
from rhodecode.tests import *

proto = 'http'
TEST_URLS = [
    ('%s://127.0.0.1' % proto, ['%s://' % proto, '127.0.0.1'],
     '%s://127.0.0.1' % proto),
    ('%s://marcink@127.0.0.1' % proto, ['%s://' % proto, '127.0.0.1'],
     '%s://127.0.0.1' % proto),
    ('%s://marcink:pass@127.0.0.1' % proto, ['%s://' % proto, '127.0.0.1'],
     '%s://127.0.0.1' % proto),
    ('%s://127.0.0.1:8080' % proto, ['%s://' % proto, '127.0.0.1', '8080'],
     '%s://127.0.0.1:8080' % proto),
    ('%s://domain.org' % proto, ['%s://' % proto, 'domain.org'],
     '%s://domain.org' % proto),
    ('%s://user:pass@domain.org:8080' % proto, ['%s://' % proto, 'domain.org',
                                                '8080'],
     '%s://domain.org:8080' % proto),
]

proto = 'https'
TEST_URLS += [
    ('%s://127.0.0.1' % proto, ['%s://' % proto, '127.0.0.1'],
     '%s://127.0.0.1' % proto),
    ('%s://marcink@127.0.0.1' % proto, ['%s://' % proto, '127.0.0.1'],
     '%s://127.0.0.1' % proto),
    ('%s://marcink:pass@127.0.0.1' % proto, ['%s://' % proto, '127.0.0.1'],
     '%s://127.0.0.1' % proto),
    ('%s://127.0.0.1:8080' % proto, ['%s://' % proto, '127.0.0.1', '8080'],
     '%s://127.0.0.1:8080' % proto),
    ('%s://domain.org' % proto, ['%s://' % proto, 'domain.org'],
     '%s://domain.org' % proto),
    ('%s://user:pass@domain.org:8080' % proto, ['%s://' % proto, 'domain.org',
                                                '8080'],
     '%s://domain.org:8080' % proto),
]


class TestLibs(unittest.TestCase):

    def test_uri_filter(self):
        from rhodecode.lib.utils2 import uri_filter

        for url in TEST_URLS:
            self.assertEqual(uri_filter(url[0]), url[1])

    def test_credentials_filter(self):
        from rhodecode.lib.utils2 import credentials_filter

        for url in TEST_URLS:
            self.assertEqual(credentials_filter(url[0]), url[2])

    def test_str2bool(self):
        from rhodecode.lib.utils2 import str2bool
        test_cases = [
            ('t', True),
            ('true', True),
            ('y', True),
            ('yes', True),
            ('on', True),
            ('1', True),
            ('Y', True),
            ('yeS', True),
            ('Y', True),
            ('TRUE', True),
            ('T', True),
            ('False', False),
            ('F', False),
            ('FALSE', False),
            ('0', False),
            ('-1', False),
            ('', False), ]

        for case in test_cases:
            self.assertEqual(str2bool(case[0]), case[1])

    def test_mention_extractor(self):
        from rhodecode.lib.utils2 import extract_mentioned_users
        sample = (
            "@first hi there @marcink here's my email marcin@email.com "
            "@lukaszb check @one_more22 it pls @ ttwelve @D[] @one@two@three "
            "@MARCIN    @maRCiN @2one_more22 @john please see this http://org.pl "
            "@marian.user just do it @marco-polo and next extract @marco_polo "
            "user.dot  hej ! not-needed maril@domain.org"
        )

        s = sorted([
        'first', 'marcink', 'lukaszb', 'one_more22', 'MARCIN', 'maRCiN', 'john',
        'marian.user', 'marco-polo', 'marco_polo'
        ], key=lambda k: k.lower())
        self.assertEqual(s, extract_mentioned_users(sample))

    def test_age(self):
        import calendar
        from rhodecode.lib.utils2 import age
        n = datetime.datetime.now()
        delt = lambda *args, **kwargs: datetime.timedelta(*args, **kwargs)
        self.assertEqual(age(n), u'just now')
        self.assertEqual(age(n - delt(seconds=1)), u'1 second ago')
        self.assertEqual(age(n - delt(seconds=60 * 2)), u'2 minutes ago')
        self.assertEqual(age(n - delt(hours=1)), u'1 hour ago')
        self.assertEqual(age(n - delt(hours=24)), u'1 day ago')
        self.assertEqual(age(n - delt(hours=24 * 5)), u'5 days ago')
        self.assertEqual(age(n - delt(hours=24 * (calendar.mdays[n.month-1] + 2))),
                         u'1 month and 2 days ago')
        self.assertEqual(age(n - delt(hours=24 * 400)), u'1 year and 1 month ago')

    def test_tag_exctrator(self):
        sample = (
            "hello pta[tag] gog [[]] [[] sda ero[or]d [me =>>< sa]"
            "[requires] [stale] [see<>=>] [see => http://url.com]"
            "[requires => url] [lang => python] [just a tag]"
            "[,d] [ => ULR ] [obsolete] [desc]]"
        )
        from rhodecode.lib.helpers import desc_stylize
        res = desc_stylize(sample)
        self.assertTrue('<div class="metatag" tag="tag">tag</div>' in res)
        self.assertTrue('<div class="metatag" tag="obsolete">obsolete</div>' in res)
        self.assertTrue('<div class="metatag" tag="stale">stale</div>' in res)
        self.assertTrue('<div class="metatag" tag="lang">python</div>' in res)
        self.assertTrue('<div class="metatag" tag="requires">requires =&gt; <a href="/url">url</a></div>' in res)
        self.assertTrue('<div class="metatag" tag="tag">tag</div>' in res)

    def test_alternative_gravatar(self):
        from rhodecode.lib.helpers import gravatar_url
        _md5 = lambda s: hashlib.md5(s).hexdigest()

        def fake_conf(**kwargs):
            from pylons import config
            config['app_conf'] = {}
            config['app_conf']['use_gravatar'] = True
            config['app_conf'].update(kwargs)
            return config

        class fake_url():
            @classmethod
            def current(cls, *args, **kwargs):
                return 'https://server.com'

        with mock.patch('pylons.url', fake_url):
            fake = fake_conf(alternative_gravatar_url='http://test.com/{email}')
            with mock.patch('pylons.config', fake):
                    from pylons import url
                    assert url.current() == 'https://server.com'
                    grav = gravatar_url(email_address='test@foo.com', size=24)
                    assert grav == 'http://test.com/test@foo.com'

            fake = fake_conf(alternative_gravatar_url='http://test.com/{email}')
            with mock.patch('pylons.config', fake):
                grav = gravatar_url(email_address='test@foo.com', size=24)
                assert grav == 'http://test.com/test@foo.com'

            fake = fake_conf(alternative_gravatar_url='http://test.com/{md5email}')
            with mock.patch('pylons.config', fake):
                em = 'test@foo.com'
                grav = gravatar_url(email_address=em, size=24)
                assert grav == 'http://test.com/%s' % (_md5(em))

            fake = fake_conf(alternative_gravatar_url='http://test.com/{md5email}/{size}')
            with mock.patch('pylons.config', fake):
                em = 'test@foo.com'
                grav = gravatar_url(email_address=em, size=24)
                assert grav == 'http://test.com/%s/%s' % (_md5(em), 24)

            fake = fake_conf(alternative_gravatar_url='{scheme}://{netloc}/{md5email}/{size}')
            with mock.patch('pylons.config', fake):
                em = 'test@foo.com'
                grav = gravatar_url(email_address=em, size=24)
                assert grav == 'https://server.com/%s/%s' % (_md5(em), 24)

