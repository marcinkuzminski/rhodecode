"""
Automatically sets the environment variable `CELERY_LOADER` to
`celerypylons.loader:PylonsLoader`.  This ensures the loader is
specified when accessing the rest of this package, and allows celery
to be installed in a webapp just by importing celerypylons::

    import celerypylons

"""
import os
import warnings

CELERYPYLONS_LOADER = 'rhodecode.lib.celerypylons.loader.PylonsLoader'
if os.environ.get('CELERY_LOADER', CELERYPYLONS_LOADER) != CELERYPYLONS_LOADER:
    warnings.warn("'CELERY_LOADER' environment variable will be overridden by celery-pylons.")
os.environ['CELERY_LOADER'] = CELERYPYLONS_LOADER
