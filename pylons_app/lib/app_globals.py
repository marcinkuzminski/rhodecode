"""The application's Globals object"""

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from vcs.utils.lazy import LazyProperty

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
        self.available_permissions = None   # propagated after init_model
        self.baseui = None                  # propagated after init_model        
        
    @LazyProperty
    def paths(self):
        if self.baseui:
            return self.baseui.configitems('paths')
    
    @LazyProperty
    def base_path(self):
        if self.baseui:
            return self.paths[0][1].replace('*', '')            
