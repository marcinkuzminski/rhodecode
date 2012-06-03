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


class RcConf(object):
    """
    RhodeCode config for API

    conf = RcConf()
    conf['key']

    """

    def __init__(self, autoload=True, autocreate=False, config=None):
        self._conf_name = CONFIG_NAME
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
        with open(self._conf_name, 'wb') as f:
            json.dump(config, f, indent=4)
            sys.stdout.write('Updated conf\n')

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


def api_call(apikey, apihost, method=None, **kw):
    """
    Api_call wrapper for RhodeCode

    :param apikey:
    :param apihost:
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
    id_ = random.randrange(1, 200)
    req = urllib2.Request('%s/_admin/api' % apihost,
                      data=json.dumps(_build_data(id_)),
                      headers={'content-type': 'text/plain'})
    print 'calling %s to %s' % (req.get_data(), apihost)
    ret = urllib2.urlopen(req)
    json_data = json.loads(ret.read())
    id_ret = json_data['id']
    _formatted_json = pprint.pformat(json_data)
    if id_ret == id_:
        print 'rhodecode said:\n%s' % (_formatted_json)
    else:
        raise Exception('something went wrong. '
                        'ID mismatch got %s, expected %s | %s' % (
                                            id_ret, id_, _formatted_json))


def argparser(argv):
    usage = ("rhodecode_api [-h] [--apikey APIKEY] [--apihost APIHOST] "
             "_create_config or METHOD <key:val> <key2:val> ...")

    parser = argparse.ArgumentParser(description='RhodeCode API cli',
                                     usage=usage)

    ## config
    group = parser.add_argument_group('config')
    group.add_argument('--apikey', help='api access key')
    group.add_argument('--apihost', help='api host')

    group = parser.add_argument_group('API')
    group.add_argument('method', metavar='METHOD', type=str,
            help='API method name to call followed by key:value attributes',
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
        conf = RcConf(autocreate=True, config={'apikey': args.apikey,
                                               'apihost': args.apihost})
        sys.stdout.write('Create new config in %s\n' % CONFIG_NAME)

    if not conf:
        conf = RcConf(autoload=True)
        if not conf:
            if not api_credentials_given:
                parser.error('Could not find config file and missing '
                             '--apikey or --apihost in params')

    apikey = args.apikey or conf['apikey']
    host = args.apihost or conf['apihost']
    method = args.method
    margs = dict(map(lambda s: s.split(':', 1), other))

    api_call(apikey, host, method, **margs)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
