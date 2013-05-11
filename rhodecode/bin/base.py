"""
Base utils for shell scripts
"""
import os
import sys
import random
import urllib2
import pprint

try:
    from rhodecode.lib.ext_json import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json

CONFIG_NAME = '.rhodecode'
FORMAT_PRETTY = 'pretty'
FORMAT_JSON = 'json'


def api_call(apikey, apihost, format, method=None, **kw):
    """
    Api_call wrapper for RhodeCode

    :param apikey:
    :param apihost:
    :param format: formatting, pretty means prints and pprint of json
     json returns unparsed json
    :param method:
    """
    def _build_data(random_id):
        """
        Builds API data with given random ID

        :param random_id:
        """
        return {
            "id": random_id,
            "api_key": apikey,
            "method": method,
            "args": kw
        }

    if not method:
        raise Exception('please specify method name !')
    id_ = random.randrange(1, 9999)
    req = urllib2.Request('%s/_admin/api' % apihost,
                      data=json.dumps(_build_data(id_)),
                      headers={'content-type': 'text/plain'})
    if format == FORMAT_PRETTY:
        sys.stdout.write('calling %s to %s \n' % (req.get_data(), apihost))
    ret = urllib2.urlopen(req)
    raw_json = ret.read()
    json_data = json.loads(raw_json)
    id_ret = json_data['id']
    _formatted_json = pprint.pformat(json_data)
    if id_ret == id_:
        if format == FORMAT_JSON:
            sys.stdout.write(str(raw_json))
        else:
            sys.stdout.write('rhodecode returned:\n%s\n' % (_formatted_json))

    else:
        raise Exception('something went wrong. '
                        'ID mismatch got %s, expected %s | %s' % (
                                            id_ret, id_, _formatted_json))


class RcConf(object):
    """
    RhodeCode config for API

    conf = RcConf()
    conf['key']

    """

    def __init__(self, config_location=None, autoload=True, autocreate=False,
                 config=None):
        HOME = os.getenv('HOME', os.getenv('USERPROFILE')) or ''
        HOME_CONF = os.path.abspath(os.path.join(HOME, CONFIG_NAME))
        self._conf_name = HOME_CONF if not config_location else config_location
        self._conf = {}
        if autocreate:
            self.make_config(config)
        if autoload:
            self._conf = self.load_config()

    def __getitem__(self, key):
        return self._conf[key]

    def __nonzero__(self):
        if self._conf:
            return True
        return False

    def __eq__(self):
        return self._conf.__eq__()

    def __repr__(self):
        return 'RcConf<%s>' % self._conf.__repr__()

    def make_config(self, config):
        """
        Saves given config as a JSON dump in the _conf_name location

        :param config:
        """
        update = False
        if os.path.exists(self._conf_name):
            update = True
        with open(self._conf_name, 'wb') as f:
            json.dump(config, f, indent=4)

        if update:
            sys.stdout.write('Updated config in %s\n' % self._conf_name)
        else:
            sys.stdout.write('Created new config in %s\n' % self._conf_name)

    def update_config(self, new_config):
        """
        Reads the JSON config updates it's values with new_config and
        saves it back as JSON dump

        :param new_config:
        """
        config = {}
        try:
            with open(self._conf_name, 'rb') as conf:
                config = json.load(conf)
        except IOError, e:
            sys.stderr.write(str(e) + '\n')

        config.update(new_config)
        self.make_config(config)

    def load_config(self):
        """
        Loads config from file and returns loaded JSON object
        """
        try:
            with open(self._conf_name, 'rb') as conf:
                return  json.load(conf)
        except IOError, e:
            #sys.stderr.write(str(e) + '\n')
            pass
