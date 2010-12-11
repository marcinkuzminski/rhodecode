"""Setup the rhodecode application"""
from rhodecode.config.environment import load_environment
from rhodecode.lib.db_manage import DbManage
import logging
import os

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup rhodecode here"""
    dbconf = conf['sqlalchemy.db1.url']
    dbmanage = DbManage(log_sql=True, dbconf=dbconf, root=conf['here'], tests=False)
    dbmanage.create_tables(override=True)
    dbmanage.set_db_version()
    dbmanage.config_prompt(None)
    dbmanage.create_default_user()
    dbmanage.admin_prompt()
    dbmanage.create_permissions()
    dbmanage.populate_default_permissions()

    load_environment(conf.global_conf, conf.local_conf, initial=True)





