from celery.loaders.base import BaseLoader
from pylons import config

to_pylons = lambda x: x.replace('_', '.').lower()
to_celery = lambda x: x.replace('.', '_').upper()

LIST_PARAMS = """CELERY_IMPORTS ADMINS ROUTES""".split()


class PylonsSettingsProxy(object):
    """Pylons Settings Proxy

    Proxies settings from pylons.config

    """
    def __getattr__(self, key):
        pylons_key = to_pylons(key)
        try:
            value = config[pylons_key]
            if key in LIST_PARAMS:return value.split()
            return self.type_converter(value)
        except KeyError:
            raise AttributeError(pylons_key)

    def get(self, key):
        try:
            return self.__getattr__(key)
        except AttributeError:
            return None

    def __getitem__(self, key):
        try:
            return self.__getattr__(key)
        except AttributeError:
            raise KeyError()

    def __setattr__(self, key, value):
        pylons_key = to_pylons(key)
        config[pylons_key] = value

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def type_converter(self, value):
        #cast to int
        if value.isdigit():
            return int(value)

        #cast to bool
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        return value

class PylonsLoader(BaseLoader):
    """Pylons celery loader

    Maps the celery config onto pylons.config

    """
    def read_configuration(self):
        self.configured = True
        return PylonsSettingsProxy()

    def on_worker_init(self):
        """
        Import task modules.
        """
        self.import_default_modules()
