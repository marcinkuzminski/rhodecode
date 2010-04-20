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
        self.cache = CacheManager(**parse_cache_config_options(config))
        self.baseui = self.make_ui('hgwebdir.config')


    def make_ui(self, path='hgwebdir.config'):        
        """
        A funcion that will read python rc files and make an ui from read options
        
        @param path: path to mercurial config file
        """
        #propagated from mercurial documentation
        sections = [
                    'alias',
                    'auth',
                    'decode/encode',
                    'defaults',
                    'diff',
                    'email',
                    'extensions',
                    'format',
                    'merge-patterns',
                    'merge-tools',
                    'hooks',
                    'http_proxy',
                    'smtp',
                    'patch',
                    'paths',
                    'profiling',
                    'server',
                    'trusted',
                    'ui',
                    'web',
                    ]
    
        repos = path
        baseui = ui.ui()
        cfg = config.config()
        cfg.read(repos)
        self.paths = cfg.items('paths')
        self.base_path = self.paths[0][1].replace('*', '')
        self.check_repo_dir(self.paths)
        self.set_statics(cfg)
    
        for section in sections:
            for k, v in cfg.items(section):
                baseui.setconfig(section, k, v)
        
        return baseui

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

