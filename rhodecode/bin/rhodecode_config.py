"""
config generator

"""
from __future__ import with_statement
import os
import sys
import uuid
import argparse
from mako.template import Template
TMPL = 'template.ini.mako'
here = os.path.dirname(os.path.abspath(__file__))

def argparser(argv):
    usage = (
      "rhodecode-config [-h] [--filename=FILENAME] [--template=TEMPLATE] \n"
      "VARS optional specify extra template variable that will be available in "
      "template. Use comma separated key=val format eg.\n"
      "key1=val1,port=5000,host=127.0.0.1,elements='a\,b\,c'\n"
    )

    parser = argparse.ArgumentParser(
        description='RhodeCode CONFIG generator with variable replacement',
        usage=usage
    )

    ## config
    group = parser.add_argument_group('CONFIG')
    group.add_argument('--filename', help='Output ini filename.')
    group.add_argument('--template', help='Mako template file to use instead of '
                                          'the default builtin template')
    group.add_argument('--raw', help='Store given mako template as raw without '
                                     'parsing. Use this to create custom template '
                                     'initially', action='store_true')
    group.add_argument('--show-defaults', help='Show all default variables for '
                                               'builtin template', action='store_true')
    args, other = parser.parse_known_args()
    return parser, args, other


def _escape_split(text, sep):
    """
    Allows for escaping of the separator: e.g. arg='foo\, bar'

    It should be noted that the way bash et. al. do command line parsing, those
    single quotes are required. a shameless ripoff from fabric project.

    """
    escaped_sep = r'\%s' % sep

    if escaped_sep not in text:
        return text.split(sep)

    before, _, after = text.partition(escaped_sep)
    startlist = before.split(sep)  # a regular split is fine here
    unfinished = startlist[-1]
    startlist = startlist[:-1]

    # recurse because there may be more escaped separators
    endlist = _escape_split(after, sep)

    # finish building the escaped value. we use endlist[0] becaue the first
    # part of the string sent in recursion is the rest of the escaped value.
    unfinished += sep + endlist[0]

    return startlist + [unfinished] + endlist[1:]  # put together all the parts

def _run(argv):
    parser, args, other = argparser(argv)
    if not len(sys.argv) > 1:
        print parser.print_help()
        sys.exit(0)
    # defaults that can be overwritten by arguments
    tmpl_stored_args = {
        'http_server': 'waitress',
        'lang': 'en',
        'database_engine': 'sqlite',
        'host': '127.0.0.1',
        'port': 5000,
        'error_aggregation_service': None
    }
    if other:
        # parse arguments, we assume only first is correct
        kwargs = {}
        for el in _escape_split(other[0], ','):
            kv = _escape_split(el, '=')
            if len(kv) == 2:
                k, v = kv
                kwargs[k] = v
        # update our template stored args
        tmpl_stored_args.update(kwargs)

    # use default that cannot be replaced
    tmpl_stored_args.update({
        'uuid': lambda: uuid.uuid4().hex,
        'here': os.path.abspath(os.curdir),
    })
    if args.show_defaults:
        for k,v in tmpl_stored_args.iteritems():
            print '%s=%s' % (k, v)
        sys.exit(0)
    try:
        # built in template
        tmpl_file = os.path.join(here, TMPL)
        if args.template:
            tmpl_file = args.template

        with open(tmpl_file, 'rb') as f:
            tmpl_data = f.read()
            if args.raw:
                tmpl = tmpl_data
            else:
                tmpl = Template(tmpl_data).render(**tmpl_stored_args)
        with open(args.filename, 'wb') as f:
            f.write(tmpl)
        print 'Wrote new config file in %s' % (os.path.abspath(args.filename))

    except Exception:
        from mako import exceptions
        print exceptions.text_error_template().render()

def main(argv=None):
    """
    Main execution function for cli

    :param argv:
    """
    if argv is None:
        argv = sys.argv

    try:
        return _run(argv)
    except Exception:
        raise


if __name__ == '__main__':
    sys.exit(main(sys.argv))
