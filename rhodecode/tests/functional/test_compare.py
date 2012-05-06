from rhodecode.tests import *

class TestCompareController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='compare', action='index'))
        # Test response...
