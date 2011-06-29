from rhodecode.tests import *
import os
from nose.plugins.skip import SkipTest

class TestSearchController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'))

        self.assertTrue('class="small" id="q" name="q" type="text"' in
                        response.body)
        # Test response...

    def test_empty_search(self):
        if os.path.isdir(self.index_location):
            raise SkipTest('skipped due to existing index')
        else:
            self.log_user()
            response = self.app.get(url(controller='search', action='index'),
                                    {'q':HG_REPO})
            self.assertTrue('There is no index to search in. '
                            'Please run whoosh indexer' in response.body)

    def test_normal_search(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'),
                                {'q':'def repo'})
        self.assertTrue('10 results' in response.body)
        self.assertTrue('Permission denied' not in response.body)

    def test_repo_search(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'),
                                {'q':'repository:%s def test' % HG_REPO})
        self.assertTrue('4 results' in response.body)
        self.assertTrue('Permission denied' not in response.body)
