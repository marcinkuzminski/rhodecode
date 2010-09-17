"""Pylons application test package

This package assumes the Pylons environment is already loaded, such as
when this script is imported from the `nosetests --with-pylons=test.ini`
command.

This module initializes the application via ``websetup`` (`paster
setup-app`) and provides the base testing objects.
"""
from unittest import TestCase

from paste.deploy import loadapp
from paste.script.appinstall import SetupCommand
from pylons import config, url
from routes.util import URLGenerator
from webtest import TestApp
import os
from pylons_app.model import meta
from pylons_app.lib.indexers import IDX_LOCATION
import logging
import shutil
log = logging.getLogger(__name__) 

import pylons.test

__all__ = ['environ', 'url', 'TestController']

# Invoke websetup with the current config file
#SetupCommand('setup-app').run([pylons.test.pylonsapp.config['__file__']])
def create_index(repo_location, full_index):
    from pylons_app.lib.indexers import daemon
    from pylons_app.lib.indexers.daemon import WhooshIndexingDaemon
    from pylons_app.lib.indexers.pidlock import DaemonLock, LockHeld
    
    try:
        l = DaemonLock()
        WhooshIndexingDaemon(repo_location=repo_location)\
            .run(full_index=full_index)
        l.release()
    except LockHeld:
        pass    
    
if os.path.exists(IDX_LOCATION):
    shutil.rmtree(IDX_LOCATION)
    
create_index('/tmp/*', True)    

environ = {}

class TestController(TestCase):

    def __init__(self, *args, **kwargs):
        wsgiapp = pylons.test.pylonsapp
        config = wsgiapp.config
        self.app = TestApp(wsgiapp)
        url._push_object(URLGenerator(config['routes.map'], environ))
        self.sa = meta.Session

        TestCase.__init__(self, *args, **kwargs)

    
    def log_user(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username':'test_admin',
                                  'password':'test'})
        assert response.status == '302 Found', 'Wrong response code from login got %s' % response.status
        assert response.session['hg_app_user'].username == 'test_admin', 'wrong logged in user'
        return response.follow()

 
