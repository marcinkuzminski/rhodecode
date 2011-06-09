# -*- coding: utf-8 -*-
"""
    rhodecode.tests.test_libs
    ~~~~~~~~~~~~~~~~~~~~~~~~~


    Package for testing varios lib/helper functions in rhodecode
    
    :created_on: Jun 9, 2011
    :copyright: (c) 2011 by marcink.
    :license: LICENSE_NAME, see LICENSE_FILE for more details.
"""



import unittest
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
        from rhodecode.lib import uri_filter

        for url in TEST_URLS:
            self.assertEqual(uri_filter(url[0]), url[1])

    def test_credentials_filter(self):
        from rhodecode.lib import credentials_filter

        for url in TEST_URLS:
            self.assertEqual(credentials_filter(url[0]), url[2])


    def test_str2bool(self):
        from rhodecode.lib import str2bool
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

