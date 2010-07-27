"""Setup the pylons_app application"""

from os.path import dirname as dn, join as jn
from pylons_app.config.environment import load_environment
from pylons_app.lib.db_manage import DbManage
import logging
import os
import sys

log = logging.getLogger(__name__)

ROOT = dn(dn(os.path.realpath(__file__)))
sys.path.append(ROOT)

def setup_app(command, conf, vars):
    """Place any commands to setup pylons_app here"""
    dbmanage = DbManage(log_sql=True)
    dbmanage.create_tables(override=True)
    dbmanage.config_prompt()
    dbmanage.admin_prompt()
    dbmanage.create_permissions()
    load_environment(conf.global_conf, conf.local_conf, initial=True)

