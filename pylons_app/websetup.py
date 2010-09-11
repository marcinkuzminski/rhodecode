"""Setup the pylons_app application"""

from os.path import dirname as dn, join as jn
from pylons_app.config.environment import load_environment
from pylons_app.lib.db_manage import DbManage
import datetime
from time import mktime
import logging
import os
import sys
import tarfile

log = logging.getLogger(__name__)

ROOT = dn(dn(os.path.realpath(__file__)))
sys.path.append(ROOT)

def setup_app(command, conf, vars):
    """Place any commands to setup pylons_app here"""
    log_sql = True
    tests = False
    
    dbname = os.path.split(conf['sqlalchemy.db1.url'])[-1]
    filename = os.path.split(conf.filename)[-1]
    
    if filename == 'tests.ini':
        uniq_suffix = str(int(mktime(datetime.datetime.now().timetuple())))
        REPO_TEST_PATH = '/tmp/hg_app_test_%s' % uniq_suffix
        
        if not os.path.isdir(REPO_TEST_PATH):
            os.mkdir(REPO_TEST_PATH)
            cur_dir = dn(os.path.abspath(__file__))
            tar = tarfile.open(jn(cur_dir,'tests',"vcs_test.tar.gz"))
            tar.extractall(REPO_TEST_PATH)
            tar.close()
            
        tests = True    
    
    dbmanage = DbManage(log_sql, dbname, tests)
    dbmanage.create_tables(override=True)
    dbmanage.config_prompt(REPO_TEST_PATH)
    dbmanage.create_default_user()
    dbmanage.admin_prompt()
    dbmanage.create_permissions()
    dbmanage.populate_default_permissions()
    load_environment(conf.global_conf, conf.local_conf, initial=True)

