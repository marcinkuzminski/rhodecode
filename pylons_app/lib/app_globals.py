"""The application's Globals object"""
#uncomment the following if you want to serve a single repo
#from mercurial.hgweb.hgweb_mod import hgweb
from mercurial.hgweb.hgwebdir_mod import hgwebdir
from mercurial.hgweb.request import wsgiapplication
class Globals(object):

    """Globals acts as a container for objects available throughout the
    life of the application

    """

    def __init__(self):
        """One instance of Globals is created during application
        initialization and is available during requests via the
        'app_globals' variable

        """
        #two ways of building the merc app i don't know 
        #the fastest one but belive the wsgiapp is better
        #self.hgapp = self.make_web_app()
        self.hgapp = wsgiapplication(self.make_web_app)

    def make_web_app(self):
        repos = "hgwebdir.config"
        hgwebapp = hgwebdir(repos)
        return hgwebapp
