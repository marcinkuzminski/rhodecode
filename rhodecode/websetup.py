"""Setup the rhodecode application"""
from rhodecode.config.environment import load_environment
from rhodecode.lib.db_manage import DbManage
import logging
import os

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup rhodecode here"""
    dbname = os.path.split(conf['sqlalchemy.db1.url'])[-1] 
    dbmanage = DbManage(log_sql=True, dbname=dbname, root=conf['here'],
                         tests=False)
    dbmanage.create_tables(override=True)
    dbmanage.config_prompt(None)
    dbmanage.create_default_user()
    dbmanage.admin_prompt()
    dbmanage.create_permissions()
    dbmanage.populate_default_permissions()
           
    load_environment(conf.global_conf, conf.local_conf, initial=True)





