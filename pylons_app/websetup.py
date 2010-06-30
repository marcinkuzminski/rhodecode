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


def setup_repository():
    log.info('Seting up repositories.config')
    fname = 'repositories.config'
    
    try:
        tmpl = open(jn(ROOT, 'pylons_app', 'config', 'repositories.config_tmpl')).read()
    except IOError:
        raise
    
    path = raw_input('Specify valid full path to your repositories'
                    ' you can change this later in repositories.config file:')
    
    if not os.path.isdir(path):
        log.error('You entered wrong path')
        sys.exit()
    
    
    path = jn(path, '*') 
    dest_path = jn(ROOT, fname)
    f = open(dest_path, 'wb')
    f.write(tmpl % {'repo_location':path})
    f.close()
    log.info('created repositories.config in %s', dest_path)
        

def setup_app(command, conf, vars):
    """Place any commands to setup pylons_app here"""
    setup_repository()
    dbmanage = DbManage(log_sql=True)
    dbmanage.create_tables(override=True)
    dbmanage.admin_prompt()
    dbmanage.create_permissions()
    load_environment(conf.global_conf, conf.local_conf)

