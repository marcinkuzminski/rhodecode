"""The application's Globals object"""

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from pylons_app.lib.utils import make_ui

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
        self.baseui = make_ui('hgwebdir.config')
        self.paths = self.baseui.configitems('paths')
        self.base_path = self.paths[0][1].replace('*', '')
        self.changeset_annotation_colors = {}
        self.available_permissions = None # propagated after init_model
