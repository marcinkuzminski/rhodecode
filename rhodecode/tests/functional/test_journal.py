from rhodecode.tests import *

class TestJournalController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='journal', action='index'))
        # Test response...
