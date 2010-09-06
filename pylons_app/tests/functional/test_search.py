from pylons_app.tests import *

class TestSearchController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'))
        print response.body
        assert 'class="small" id="q" name="q" type="text"' in response.body,'Search box content error'
        # Test response...

    def test_empty_search(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'),{'q':'vcs_test'})
        assert 'There is no index to search in. Please run whoosh indexer' in response.body,'No error message about empty index'