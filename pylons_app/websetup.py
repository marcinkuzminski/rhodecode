"""Setup the pylons_app application"""
import logging
from pylons_app.config.environment import load_environment
log = logging.getLogger(__name__)


def setup_app(command, conf, vars):
    """Place any commands to setup pylons_app here"""
    load_environment(conf.global_conf, conf.local_conf)
