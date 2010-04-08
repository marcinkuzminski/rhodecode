"""The application's Globals object"""
#uncomment the following if you want to serve a single repo
#from mercurial.hgweb.hgweb_mod import hgweb
from mercurial.hgweb.hgwebdir_mod import hgwebdir
from mercurial import templater
from mercurial.hgweb.request import wsgiapplication
from mercurial import ui, config
import os
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

class Globals(object):

    """Globals acts as a container for objects available throughout the
    life of the application

    """

    def __init__(self, config):
        """One instance of Globals is created during application
        initialization and is available during requests via the
        'app_globals' variable

        """
        #two ways of building the merc app i don't know 
        #the fastest one but belive the wsgiapp is better
        #self.hgapp = self.make_web_app()
        self.cache = CacheManager(**parse_cache_config_options(config))
        self.hgapp = wsgiapplication(self.make_web_app)

    def make_web_app(self):
        repos = "hgwebdir.config"
        baseui = ui.ui()
        cfg = config.config()
        cfg.read(repos)
        paths = cfg.items('paths')
        self.paths = paths
        self.check_repo_dir(paths)
        
        self.set_statics(cfg)

        for k, v in cfg.items('web'):
            baseui.setconfig('web', k, v)
        #magic trick to make our custom template dir working
        templater.path.append(cfg.get('web', 'templates', None))

        #baseui.setconfig('web', 'description', '')
        #baseui.setconfig('web', 'name', '')
        #baseui.setconfig('web', 'contact', '')
        #baseui.setconfig('web', 'allow_archive', '')
        #baseui.setconfig('web', 'style', 'monoblue_plain')
        #baseui.setconfig('web', 'baseurl', '')
        #baseui.setconfig('web', 'staticurl', '')
        
        hgwebapp = hgwebdir(paths, baseui=baseui)
        return hgwebapp


    def set_statics(self, cfg):
        '''
        set's the statics for use in mako templates
        @param cfg:
        '''
        self.statics = cfg.get('web', 'staticurl', '/static')
        if not self.statics.endswith('/'):
            self.statics += '/'


    def check_repo_dir(self, paths):
        repos_path = paths[0][1].split('/')
        if repos_path[-1] in ['*', '**']:
            repos_path = repos_path[:-1]
        if repos_path[0] != '/':
            repos_path[0] = '/'
        if not os.path.isdir(os.path.join(*repos_path)):
            raise Exception('Not a valid repository in %s' % paths[0][1])

