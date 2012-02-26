"""Pylons middleware initialization"""

from beaker.middleware import SessionMiddleware
from routes.middleware import RoutesMiddleware
from paste.cascade import Cascade
from paste.registry import RegistryManager
from paste.urlparser import StaticURLParser
from paste.deploy.converters import asbool
from paste.gzipper import make_gzip_middleware

from pylons.middleware import ErrorHandler, StatusCodeRedirect
from pylons.wsgiapp import PylonsApp

from rhodecode.lib.middleware.simplehg import SimpleHg
from rhodecode.lib.middleware.simplegit import SimpleGit
from rhodecode.lib.middleware.https_fixup import HttpsFixup
from rhodecode.config.environment import load_environment


def make_app(global_conf, full_stack=True, static_files=True, **app_conf):
    """Create a Pylons WSGI application and return it

    ``global_conf``
        The inherited configuration for this application. Normally from
        the [DEFAULT] section of the Paste ini file.

    ``full_stack``
        Whether or not this application provides a full WSGI stack (by
        default, meaning it handles its own exceptions and errors).
        Disable full_stack when this application is "managed" by
        another WSGI middleware.

    ``app_conf``
        The application's local configuration. Normally specified in
        the [app:<name>] section of the Paste ini file (where <name>
        defaults to main).

    """
    # Configure the Pylons environment
    config = load_environment(global_conf, app_conf)

    # The Pylons WSGI app
    app = PylonsApp(config=config)

    # Routing/Session/Cache Middleware
    app = RoutesMiddleware(app, config['routes.map'])
    app = SessionMiddleware(app, config)

    # CUSTOM MIDDLEWARE HERE (filtered by error handling middlewares)
    if asbool(config['pdebug']):
        from rhodecode.lib.profiler import ProfilingMiddleware
        app = ProfilingMiddleware(app)

    if asbool(full_stack):

        # Handle Python exceptions
        app = ErrorHandler(app, global_conf, **config['pylons.errorware'])

        # we want our low level middleware to get to the request ASAP. We don't
        # need any pylons stack middleware in them
        app = SimpleHg(app, config)
        app = SimpleGit(app, config)

        # Display error documents for 401, 403, 404 status codes (and
        # 500 when debug is disabled)
        if asbool(config['debug']):
            app = StatusCodeRedirect(app)
        else:
            app = StatusCodeRedirect(app, [400, 401, 403, 404, 500])

    #enable https redirets based on HTTP_X_URL_SCHEME set by proxy
    app = HttpsFixup(app, config)

    # Establish the Registry for this application
    app = RegistryManager(app)

    if asbool(static_files):
        # Serve static files
        static_app = StaticURLParser(config['pylons.paths']['static_files'])
        app = Cascade([static_app, app])
        app = make_gzip_middleware(app, global_conf, compress_level=1)

    app.config = config

    return app
