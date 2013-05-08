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


class TestLibs(BaseTestCase):

    @parameterized.expand(TEST_URLS)
    def test_uri_filter(self, test_url, expected, expected_creds):
        from rhodecode.lib.utils2 import uri_filter
        self.assertEqual(uri_filter(test_url), expected)

    @parameterized.expand(TEST_URLS)
    def test_credentials_filter(self, test_url, expected, expected_creds):
        from rhodecode.lib.utils2 import credentials_filter
        self.assertEqual(credentials_filter(test_url), expected_creds)

    @parameterized.expand([('t', True),
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
                           ('', False)
    ])
    def test_str2bool(self, str_bool, expected):
        from rhodecode.lib.utils2 import str2bool
        self.assertEqual(str2bool(str_bool), expected)

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

    @parameterized.expand([
        (dict(), u'just now'),
        (dict(seconds= -1), u'1 second ago'),
        (dict(seconds= -60 * 2), u'2 minutes ago'),
        (dict(hours= -1), u'1 hour ago'),
        (dict(hours= -24), u'1 day ago'),
        (dict(hours= -24 * 5), u'5 days ago'),
        (dict(months= -1), u'1 month ago'),
        (dict(months= -1, days= -2), u'1 month and 2 days ago'),
        (dict(years= -1, months= -1), u'1 year and 1 month ago'),
    ])
    def test_age(self, age_args, expected):
        from rhodecode.lib.utils2 import age
        from dateutil import relativedelta
        n = datetime.datetime(year=2012, month=5, day=17)
        delt = lambda *args, **kwargs: relativedelta.relativedelta(*args, **kwargs)
        self.assertEqual(age(n + delt(**age_args), now=n), expected)

    @parameterized.expand([

        (dict(), u'just now'),
        (dict(seconds=1), u'in 1 second'),
        (dict(seconds=60 * 2), u'in 2 minutes'),
        (dict(hours=1), u'in 1 hour'),
        (dict(hours=24), u'in 1 day'),
        (dict(hours=24 * 5), u'in 5 days'),
        (dict(months=1), u'in 1 month'),
        (dict(months=1, days=1), u'in 1 month and 1 day'),
        (dict(years=1, months=1), u'in 1 year and 1 month')
    ])
    def test_age_in_future(self, age_args, expected):
        from rhodecode.lib.utils2 import age
        from dateutil import relativedelta
        n = datetime.datetime(year=2012, month=5, day=17)
        delt = lambda *args, **kwargs: relativedelta.relativedelta(*args, **kwargs)
        self.assertEqual(age(n + delt(**age_args), now=n), expected)

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

    def _quick_url(self, text, tmpl="""<a class="revision-link" href="%s">%s</a>""", url_=None):
        """
        Changes `some text url[foo]` => `some text <a href="/">foo</a>

        :param text:
        """
        import re
        # quickly change expected url[] into a link
        URL_PAT = re.compile(r'(?:url\[)(.+?)(?:\])')

        def url_func(match_obj):
            _url = match_obj.groups()[0]
            return tmpl % (url_ or '/some-url', _url)
        return URL_PAT.sub(url_func, text)

    @parameterized.expand([
      ("",
       ""),
      ("git-svn-id: https://svn.apache.org/repos/asf/libcloud/trunk@1441655 13f79535-47bb-0310-9956-ffa450edef68",
       "git-svn-id: https://svn.apache.org/repos/asf/libcloud/trunk@1441655 13f79535-47bb-0310-9956-ffa450edef68"),
      ("from rev 000000000000",
       "from rev url[000000000000]"),
      ("from rev 000000000000123123 also rev 000000000000",
       "from rev url[000000000000123123] also rev url[000000000000]"),
      ("this should-000 00",
       "this should-000 00"),
      ("longtextffffffffff rev 123123123123",
       "longtextffffffffff rev url[123123123123]"),
      ("rev ffffffffffffffffffffffffffffffffffffffffffffffffff",
       "rev ffffffffffffffffffffffffffffffffffffffffffffffffff"),
      ("ffffffffffff some text traalaa",
       "url[ffffffffffff] some text traalaa"),
       ("""Multi line
       123123123123
       some text 123123123123
       sometimes !
       """,
       """Multi line
       url[123123123123]
       some text url[123123123123]
       sometimes !
       """)
    ])
    def test_urlify_changesets(self, sample, expected):
        def fake_url(self, *args, **kwargs):
            return '/some-url'

        expected = self._quick_url(expected)

        with mock.patch('pylons.url', fake_url):
            from rhodecode.lib.helpers import urlify_changesets
            self.assertEqual(urlify_changesets(sample, 'repo_name'), expected)

    @parameterized.expand([
      ("",
       "",
       ""),
      ("https://svn.apache.org/repos",
       "url[https://svn.apache.org/repos]",
       "https://svn.apache.org/repos"),
      ("http://svn.apache.org/repos",
       "url[http://svn.apache.org/repos]",
       "http://svn.apache.org/repos"),
      ("from rev a also rev http://google.com",
       "from rev a also rev url[http://google.com]",
       "http://google.com"),
       ("""Multi line
       https://foo.bar.com
       some text lalala""",
       """Multi line
       url[https://foo.bar.com]
       some text lalala""",
       "https://foo.bar.com")
    ])
    def test_urlify_test(self, sample, expected, url_):
        from rhodecode.lib.helpers import urlify_text
        expected = self._quick_url(expected,
                                   tmpl="""<a href="%s">%s</a>""", url_=url_)
        self.assertEqual(urlify_text(sample), expected)
