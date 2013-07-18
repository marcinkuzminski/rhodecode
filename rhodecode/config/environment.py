"""Pylons environment configuration"""

import os
import logging
import shlex
import rhodecode

from mako.lookup import TemplateLookup
from pylons.configuration import PylonsConfig
from pylons.error import handle_mako_error

# don't remove this import it does magic for celery
from rhodecode.lib import celerypylons

import rhodecode.lib.app_globals as app_globals

from rhodecode.config.routing import make_map

from rhodecode.lib import helpers
from rhodecode.lib.auth import set_available_permissions
from rhodecode.lib.utils import repo2db_mapper, make_ui, set_rhodecode_config,\
    load_rcextensions, check_git_version, set_vcs_config
from rhodecode.lib.utils2 import engine_from_config, str2bool
from rhodecode.lib.db_manage import DbManage
from rhodecode.model import init_model
from rhodecode.model.scm import ScmModel

log = logging.getLogger(__name__)


def load_environment(global_conf, app_conf, initial=False):
    """
    Configure the Pylons environment via the ``pylons.config``
    object
    """
    config = PylonsConfig()

    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(
        root=root,
        controllers=os.path.join(root, 'controllers'),
        static_files=os.path.join(root, 'public'),
        templates=[os.path.join(root, 'templates')]
    )

    # Allow to override Mako templates
    extra_templates = app_conf.get('extra_templates')
    if extra_templates:
        extra_templates = shlex.split(extra_templates)
        paths['templates'].extend(extra_templates)

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package='rhodecode', paths=paths)

    # store some globals into rhodecode
    rhodecode.CELERY_ON = str2bool(config['app_conf'].get('use_celery'))
    rhodecode.CELERY_EAGER = str2bool(config['app_conf'].get('celery.always.eager'))

    config['routes.map'] = make_map(config)
    config['pylons.app_globals'] = app_globals.Globals(config)
    config['pylons.h'] = helpers
    rhodecode.CONFIG = config

    load_rcextensions(root_path=config['here'])

    # Setup cache object as early as possible
    import pylons
    pylons.cache._push_object(config['pylons.app_globals'].cache)

    # Create the Mako TemplateLookup, with the default auto-escaping
    config['pylons.app_globals'].mako_lookup = TemplateLookup(
        directories=paths['templates'],
        error_handler=handle_mako_error,
        module_directory=os.path.join(app_conf['cache_dir'], 'templates'),
        input_encoding='utf-8', default_filters=['escape'],
        imports=['from webhelpers.html import escape'])

    # sets the c attribute access when don't existing attribute are accessed
    config['pylons.strict_tmpl_context'] = True
    test = os.path.split(config['__file__'])[-1] == 'test.ini'
    if test:
        if os.environ.get('TEST_DB'):
            # swap config if we pass enviroment variable
            config['sqlalchemy.db1.url'] = os.environ.get('TEST_DB')

        from rhodecode.lib.utils import create_test_env, create_test_index
        from rhodecode.tests import  TESTS_TMP_PATH
        # set RC_NO_TMP_PATH=1 to disable re-creating the database and
        # test repos
        if not int(os.environ.get('RC_NO_TMP_PATH', 0)):
            create_test_env(TESTS_TMP_PATH, config)
        # set RC_WHOOSH_TEST_DISABLE=1 to disable whoosh index during tests
        if not int(os.environ.get('RC_WHOOSH_TEST_DISABLE', 0)):
            create_test_index(TESTS_TMP_PATH, config, True)

    DbManage.check_waitress()
    # MULTIPLE DB configs
    # Setup the SQLAlchemy database engine
    sa_engine_db1 = engine_from_config(config, 'sqlalchemy.db1.')
    init_model(sa_engine_db1)

    set_available_permissions(config)
    repos_path = make_ui('db').configitems('paths')[0][1]
    config['base_path'] = repos_path
    set_rhodecode_config(config)

    instance_id = rhodecode.CONFIG.get('instance_id')
    if instance_id == '*':
        instance_id = '%s-%s' % (os.uname()[1], os.getpid())
        rhodecode.CONFIG['instance_id'] = instance_id

    # CONFIGURATION OPTIONS HERE (note: all config options will override
    # any Pylons config options)

    # store config reference into our module to skip import magic of
    # pylons
    rhodecode.CONFIG.update(config)
    set_vcs_config(rhodecode.CONFIG)

    #check git version
    check_git_version()

    if str2bool(config.get('initial_repo_scan', True)):
        repo2db_mapper(ScmModel().repo_scan(repos_path),
                       remove_obsolete=False, install_git_hook=False)
    return config
