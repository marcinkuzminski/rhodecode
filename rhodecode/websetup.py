"""Setup the rhodecode application"""
from os.path import dirname as dn, join as jn
from rhodecode.config.environment import load_environment
from rhodecode.lib.db_manage import DbManage
import logging
import os
import shutil

log = logging.getLogger(__name__)
ROOT = dn(os.path.realpath(__file__))

def setup_app(command, conf, vars):
    """Place any commands to setup rhodecode here"""
    print dn(os.path.realpath(__file__))
    print(ROOT)
    dbname = os.path.split(conf['sqlalchemy.db1.url'])[-1] 
    dbmanage = DbManage(log_sql=True, dbname=dbname, root=conf['here'],
                         tests=False)
    dbmanage.create_tables(override=True)
    dbmanage.config_prompt(None)
    dbmanage.create_default_user()
    dbmanage.admin_prompt()
    dbmanage.create_permissions()
    dbmanage.populate_default_permissions()
    
    celeryconfig_file = 'celeryconfig.py'
    
    celeryconfig_path = jn(ROOT, celeryconfig_file)
    
        
    if not os.path.isfile(jn(conf['here'], celeryconfig_file)):
        try:
            shutil.copy(celeryconfig_path, conf['here'])
        except IOError:
            log.error('failed to copy celeryconfig.py from source %s ' 
                      ' to this directory please copy it manually ',
                      celeryconfig_path)
        else:       
            load_environment(conf.global_conf, conf.local_conf, initial=True)





