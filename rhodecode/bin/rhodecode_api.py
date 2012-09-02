# -*- coding: utf-8 -*-
"""
    rhodecode.bin.backup_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Api CLI client for RhodeCode

    :created_on: Jun 3, 2012
    :author: marcink
    :copyright: (C) 2010-2012 Marcin Kuzminski <marcin@python-works.com>
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement
import os
import sys
import random
import urllib2
import pprint
import argparse

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


class RcConf(object):
    """
    RhodeCode config for API

    conf = RcConf()
    conf['key']

    """

    def __init__(self, config_location=None, autoload=True, autocreate=False,
                 config=None):
        self._conf_name = CONFIG_NAME if not config_location else config_location
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
        :type config:
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
        :type random_id:
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


def argparser(argv):
    usage = (
      "rhodecode_api [-h] [--format=FORMAT] [--apikey=APIKEY] [--apihost=APIHOST] "
      " [--config=CONFIG] "
      "_create_config or METHOD <key:val> <key2:val> ..."
    )

    parser = argparse.ArgumentParser(description='RhodeCode API cli',
                                     usage=usage)

    ## config
    group = parser.add_argument_group('config')
    group.add_argument('--apikey', help='api access key')
    group.add_argument('--apihost', help='api host')
    group.add_argument('--config', help='config file')

    group = parser.add_argument_group('API')
    group.add_argument('method', metavar='METHOD', type=str,
            help='API method name to call followed by key:value attributes',
    )
    group.add_argument('--format', dest='format', type=str,
            help='output format default: `pretty` can '
                 'be also `%s`' % FORMAT_JSON,
            default=FORMAT_PRETTY
    )
    args, other = parser.parse_known_args()
    return parser, args, other


def main(argv=None):
    """
    Main execution function for cli

    :param argv:
    :type argv:
    """
    if argv is None:
        argv = sys.argv

    conf = None
    parser, args, other = argparser(argv)

    api_credentials_given = (args.apikey and args.apihost)
    if args.method == '_create_config':
        if not api_credentials_given:
            raise parser.error('_create_config requires --apikey and --apihost')
        conf = RcConf(config_location=args.config,
                      autocreate=True, config={'apikey': args.apikey,
                                               'apihost': args.apihost})

    if not conf:
        conf = RcConf(config_location=args.config, autoload=True)
        if not conf:
            if not api_credentials_given:
                parser.error('Could not find config file and missing '
                             '--apikey or --apihost in params')

    apikey = args.apikey or conf['apikey']
    host = args.apihost or conf['apihost']
    method = args.method
    if method == '_create_config':
        sys.exit()

    try:
        margs = dict(map(lambda s: s.split(':', 1), other))
    except:
        sys.stderr.write('Error parsing arguments \n')
        sys.exit()

    api_call(apikey, host, args.format, method, **margs)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
