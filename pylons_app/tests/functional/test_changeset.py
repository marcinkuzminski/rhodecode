from pylons_app.tests import *

class TestChangesetController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='changeset', action='index'))
        # Test response...
