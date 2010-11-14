from rhodecode.tests import *
import os
from nose.plugins.skip import SkipTest

class TestSearchController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'))
        print response.body
        assert 'class="small" id="q" name="q" type="text"' in response.body, 'Search box content error'
        # Test response...

    def test_empty_search(self):
        if os.path.isdir(self.index_location):
            raise SkipTest('skipped due to existing index')
        else:
            self.log_user()
            response = self.app.get(url(controller='search', action='index'), {'q':HG_REPO})
            assert 'There is no index to search in. Please run whoosh indexer' in response.body, 'No error message about empty index'

    def test_normal_search(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'), {'q':'def repo'})
        print response.body
        assert '10 results' in response.body, 'no message about proper search results'
        assert 'Permission denied' not in response.body, 'Wrong permissions settings for that repo and user'


    def test_repo_search(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'), {'q':'repository:%s def test' % HG_REPO})
        print response.body
        assert '4 results' in response.body, 'no message about proper search results'
        assert 'Permission denied' not in response.body, 'Wrong permissions settings for that repo and user'

