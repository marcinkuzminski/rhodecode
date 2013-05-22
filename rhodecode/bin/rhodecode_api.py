# -*- coding: utf-8 -*-
"""
    rhodecode.bin.api
    ~~~~~~~~~~~~~~~~~

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
import sys
import argparse

from rhodecode.bin.base import json, api_call, RcConf, FORMAT_JSON, FORMAT_PRETTY


def argparser(argv):
    usage = (
      "rhodecode-api [-h] [--format=FORMAT] [--apikey=APIKEY] [--apihost=APIHOST] "
      "[--config=CONFIG] [--save-config] "
      "METHOD <key:val> <key2:val> ...\n"
      "Create config file: rhodecode-gist --apikey=<key> --apihost=http://rhodecode.server --save-config"
    )

    parser = argparse.ArgumentParser(description='RhodeCode API cli',
                                     usage=usage)

    ## config
    group = parser.add_argument_group('config')
    group.add_argument('--apikey', help='api access key')
    group.add_argument('--apihost', help='api host')
    group.add_argument('--config', help='config file')
    group.add_argument('--save-config', action='store_true', help='save the given config into a file')

    group = parser.add_argument_group('API')
    group.add_argument('method', metavar='METHOD', nargs='?', type=str, default=None,
            help='API method name to call followed by key:value attributes',
    )
    group.add_argument('--format', dest='format', type=str,
            help='output format default: `%s` can '
                 'be also `%s`' % (FORMAT_PRETTY, FORMAT_JSON),
            default=FORMAT_PRETTY
    )
    args, other = parser.parse_known_args()
    return parser, args, other


def main(argv=None):
    """
    Main execution function for cli

    :param argv:
    """
    if argv is None:
        argv = sys.argv

    conf = None
    parser, args, other = argparser(argv)

    api_credentials_given = (args.apikey and args.apihost)
    if args.save_config:
        if not api_credentials_given:
            raise parser.error('--save-config requires --apikey and --apihost')
        conf = RcConf(config_location=args.config,
                      autocreate=True, config={'apikey': args.apikey,
                                               'apihost': args.apihost})
        sys.exit()

    if not conf:
        conf = RcConf(config_location=args.config, autoload=True)
        if not conf:
            if not api_credentials_given:
                parser.error('Could not find config file and missing '
                             '--apikey or --apihost in params')

    apikey = args.apikey or conf['apikey']
    apihost = args.apihost or conf['apihost']
    method = args.method

    # if we don't have method here it's an error
    if not method:
        parser.error('Please specify method name')

    try:
        margs = dict(map(lambda s: s.split(':', 1), other))
    except Exception:
        sys.stderr.write('Error parsing arguments \n')
        sys.exit()
    if args.format == FORMAT_PRETTY:
        print 'Calling method %s => %s' % (method, apihost)

    json_resp = api_call(apikey, apihost, method, **margs)
    if json_resp['error']:
        json_data = json_resp['error']
    else:
        json_data = json_resp['result']
    if args.format == FORMAT_JSON:
        print json.dumps(json_data)
    elif args.format == FORMAT_PRETTY:
        print 'Server response \n%s' % (
                json.dumps(json_data, indent=4, sort_keys=True))
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
