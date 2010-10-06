"""Setup the rhodecode application"""

from os.path import dirname as dn
from rhodecode.config.environment import load_environment
from rhodecode.lib.db_manage import DbManage
import logging
import os
import sys

log = logging.getLogger(__name__)

ROOT = dn(dn(os.path.realpath(__file__)))
sys.path.append(ROOT)


def setup_app(command, conf, vars):
    """Place any commands to setup rhodecode here"""
    log_sql = True
    tests = False
    REPO_TEST_PATH = None
    
    dbname = os.path.split(conf['sqlalchemy.db1.url'])[-1] 
    
    dbmanage = DbManage(log_sql, dbname, tests)
    dbmanage.create_tables(override=True)
    dbmanage.config_prompt(REPO_TEST_PATH)
    dbmanage.create_default_user()
    dbmanage.admin_prompt()
    dbmanage.create_permissions()
    dbmanage.populate_default_permissions()
    load_environment(conf.global_conf, conf.local_conf, initial=True)

