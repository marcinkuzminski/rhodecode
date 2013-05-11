# -*- coding: utf-8 -*-
"""
    rhodecode.bin.gist
    ~~~~~~~~~~~~~~~~~~

    Gist CLI client for RhodeCode

    :created_on: May 9, 2013
    :author: marcink
    :copyright: (C) 2010-2013 Marcin Kuzminski <marcin@python-works.com>
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
import stat
import argparse
import fileinput

from rhodecode.bin.base import api_call, RcConf


def argparser(argv):
    usage = (
      "rhodecode-gist [-h] [--format=FORMAT] [--apikey=APIKEY] [--apihost=APIHOST] "
      "[--config=CONFIG] [--save-config] "
      "[filename or stdin use - for terminal stdin ]\n"
      "Create config file: rhodecode-gist --apikey=<key> --apihost=http://rhodecode.server --save-config"
    )

    parser = argparse.ArgumentParser(description='RhodeCode Gist cli',
                                     usage=usage)

    ## config
    group = parser.add_argument_group('config')
    group.add_argument('--apikey', help='api access key')
    group.add_argument('--apihost', help='api host')
    group.add_argument('--config', help='config file')
    group.add_argument('--save-config', action='store_true',
                       help='save the given config into a file')

    group = parser.add_argument_group('GIST')
    group.add_argument('-f', '--filename', help='set uploaded gist filename')
    group.add_argument('-p', '--private', action='store_true',
                       help='Create private Gist')
    group.add_argument('-d', '--description', help='Gist description')
    group.add_argument('-l', '--lifetime', metavar='MINUTES',
                       help='Gist lifetime in minutes, -1 (Default) is forever')

    args, other = parser.parse_known_args()
    return parser, args, other


def _run(argv):
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
    host = args.apihost or conf['apihost']
    DEFAULT_FILENAME = 'gistfile1.txt'
    if other:
        # skip multifiles for now
        filename = other[0]
        if filename == '-':
            filename = DEFAULT_FILENAME
            gist_content = ''
            for line in fileinput.input():
                gist_content += line
        else:
            with open(filename, 'rb') as f:
                gist_content = f.read()

    else:
        filename = DEFAULT_FILENAME
        gist_content = None
        # little bit hacky but cross platform check where the
        # stdin comes from we skip the terminal case it can be handled by '-'
        mode = os.fstat(0).st_mode
        if stat.S_ISFIFO(mode):
            # "stdin is piped"
            gist_content = sys.stdin.read()
        elif stat.S_ISREG(mode):
            # "stdin is redirected"
            gist_content = sys.stdin.read()
        else:
            # "stdin is terminal"
            pass

    # make sure we don't upload binary stuff
    if gist_content and '\0' in gist_content:
        raise Exception('Error: binary files upload is not possible')

    filename = os.path.basename(args.filename or filename)
    if gist_content:
        files = {
            filename: {
                'content': gist_content,
                'lexer': None
            }
        }

        margs = dict(
            gist_lifetime=args.lifetime,
            gist_description=args.description,
            gist_type='private' if args.private else 'public',
            files=files
        )

        api_call(apikey, host, 'json', 'create_gist', **margs)
    return 0


def main(argv=None):
    """
    Main execution function for cli

    :param argv:
    """
    if argv is None:
        argv = sys.argv

    try:
        return _run(argv)
    except Exception, e:
        print e
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
