"""Pylons environment configuration"""
import logging
import os
from pylons import config
from mako.lookup import TemplateLookup
from pylons.error import handle_mako_error
import pylons_app.lib.app_globals as app_globals
import pylons_app.lib.helpers
from pylons_app.config.routing import make_map

log = logging.getLogger(__name__)

def load_environment(global_conf, app_conf):
    """Configure the Pylons environment via the ``pylons.config``
    object
    """
    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root = root,
                 controllers = os.path.join(root, 'controllers'),
                 static_files = os.path.join(root, 'public'),
                 templates = [os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package = 'pylons_app',
                    template_engine = 'mako', paths = paths)

    config['routes.map'] = make_map()
    config['pylons.g'] = app_globals.Globals()
    config['pylons.h'] = pylons_app.lib.helpers

    # Create the Mako TemplateLookup, with the default auto-escaping
    config['pylons.g'].mako_lookup = TemplateLookup(
        directories = paths['templates'],
        error_handler = handle_mako_error,
        module_directory = os.path.join(app_conf['cache_dir'], 'templates'),
        input_encoding = 'utf-8', default_filters = ['escape'],
        imports = ['from webhelpers.html import escape'])

    # Customize templating options via this variable
    tmpl_options = config['buffet.template_options']

    # CONFIGURATION OPTIONS HERE (note: all config options will override
    # any Pylons config options)
