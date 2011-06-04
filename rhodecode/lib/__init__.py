# -*- coding: utf-8 -*-
"""
    rhodecode.lib.__init__
    ~~~~~~~~~~~~~~~~~~~~~~~

    Some simple helper functions

    :created_on: Jan 5, 2011
    :author: marcink
    :copyright: (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
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


def __get_lem():
    from pygments import lexers
    from string import lower
    from collections import defaultdict

    d = defaultdict(lambda: [])

    def __clean(s):
        s = s.lstrip('*')
        s = s.lstrip('.')

        if s.find('[') != -1:
            exts = []
            start, stop = s.find('['), s.find(']')

            for suffix in s[start + 1:stop]:
                exts.append(s[:s.find('[')] + suffix)
            return map(lower, exts)
        else:
            return map(lower, [s])

    for lx, t in sorted(lexers.LEXERS.items()):
        m = map(__clean, t[-2])
        if m:
            m = reduce(lambda x, y: x + y, m)
            for ext in m:
                desc = lx.replace('Lexer', '')
                d[ext].append(desc)

    return dict(d)

# language map is also used by whoosh indexer, which for those specified
# extensions will index it's content
LANGUAGES_EXTENSIONS_MAP = __get_lem()

# Additional mappings that are not present in the pygments lexers
# NOTE: that this will overide any mappings in LANGUAGES_EXTENSIONS_MAP
ADDITIONAL_MAPPINGS = {'xaml': 'XAML'}

LANGUAGES_EXTENSIONS_MAP.update(ADDITIONAL_MAPPINGS)


def str2bool(_str):
    """
    returs True/False value from given string, it tries to translate the
    string into boolean

    :param _str: string value to translate into boolean
    :rtype: boolean
    :returns: boolean from given string
    """
    if _str is None:
        return False
    if _str in (True, False):
        return _str
    _str = str(_str).strip().lower()
    return _str in ('t', 'true', 'y', 'yes', 'on', '1')


def convert_line_endings(temp, mode):
    from string import replace
    #modes:  0 - Unix, 1 - Mac, 2 - DOS
    if mode == 0:
            temp = replace(temp, '\r\n', '\n')
            temp = replace(temp, '\r', '\n')
    elif mode == 1:
            temp = replace(temp, '\r\n', '\r')
            temp = replace(temp, '\n', '\r')
    elif mode == 2:
            import re
            temp = re.sub("\r(?!\n)|(?<!\r)\n", "\r\n", temp)
    return temp


def detect_mode(line, default):
    """
    Detects line break for given line, if line break couldn't be found
    given default value is returned

    :param line: str line
    :param default: default
    :rtype: int
    :return: value of line end on of 0 - Unix, 1 - Mac, 2 - DOS
    """
    if line.endswith('\r\n'):
        return 2
    elif line.endswith('\n'):
        return 0
    elif line.endswith('\r'):
        return 1
    else:
        return default


def generate_api_key(username, salt=None):
    """
    Generates unique API key for given username,if salt is not given
    it'll be generated from some random string

    :param username: username as string
    :param salt: salt to hash generate KEY
    :rtype: str
    :returns: sha1 hash from username+salt
    """
    from tempfile import _RandomNameSequence
    import hashlib

    if salt is None:
        salt = _RandomNameSequence().next()

    return hashlib.sha1(username + salt).hexdigest()


def safe_unicode(_str, from_encoding='utf8'):
    """
    safe unicode function. In case of UnicodeDecode error we try to return
    unicode with errors replace

    :param _str: string to decode
    :rtype: unicode
    :returns: unicode object
    """

    if isinstance(_str, unicode):
        return _str

    try:
        u_str = unicode(_str, from_encoding)
    except UnicodeDecodeError:
        u_str = unicode(_str, from_encoding, 'replace')

    return u_str


def engine_from_config(configuration, prefix='sqlalchemy.', **kwargs):
    """
    Custom engine_from_config functions that makes sure we use NullPool for
    file based sqlite databases. This prevents errors on sqlite. This only 
    applies to sqlalchemy versions < 0.7.0

    """
    import sqlalchemy
    from sqlalchemy import engine_from_config as efc
    import logging

    if int(sqlalchemy.__version__.split('.')[1]) < 7:

        # This solution should work for sqlalchemy < 0.7.0, and should use
        # proxy=TimerProxy() for execution time profiling

        from sqlalchemy.pool import NullPool
        url = configuration[prefix + 'url']

        if url.startswith('sqlite'):
            kwargs.update({'poolclass': NullPool})
        return efc(configuration, prefix, **kwargs)
    else:
        import time
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        log = logging.getLogger('timerproxy')
        BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = xrange(30, 38)
        engine = efc(configuration, prefix, **kwargs)

        def color_sql(sql):
            COLOR_SEQ = "\033[1;%dm"
            COLOR_SQL = YELLOW
            normal = '\x1b[0m'
            return ''.join([COLOR_SEQ % COLOR_SQL, sql, normal])

        if configuration['debug']:
            #attach events only for debug configuration

            def before_cursor_execute(conn, cursor, statement,
                                    parameters, context, executemany):
                context._query_start_time = time.time()
                log.info(color_sql(">>>>> STARTING QUERY >>>>>"))


            def after_cursor_execute(conn, cursor, statement,
                                    parameters, context, executemany):
                total = time.time() - context._query_start_time
                log.info(color_sql("<<<<< TOTAL TIME: %f <<<<<" % total))

            event.listen(engine, "before_cursor_execute",
                         before_cursor_execute)
            event.listen(engine, "after_cursor_execute",
                         after_cursor_execute)

    return engine


def age(curdate):
    """
    turns a datetime into an age string.
    
    :param curdate: datetime object
    :rtype: unicode
    :returns: unicode words describing age
    """

    from datetime import datetime
    from webhelpers.date import time_ago_in_words

    _ = lambda s:s

    if not curdate:
        return ''

    agescales = [(_(u"year"), 3600 * 24 * 365),
                 (_(u"month"), 3600 * 24 * 30),
                 (_(u"day"), 3600 * 24),
                 (_(u"hour"), 3600),
                 (_(u"minute"), 60),
                 (_(u"second"), 1), ]

    age = datetime.now() - curdate
    age_seconds = (age.days * agescales[2][1]) + age.seconds
    pos = 1
    for scale in agescales:
        if scale[1] <= age_seconds:
            if pos == 6:pos = 5
            return '%s %s' % (time_ago_in_words(curdate,
                                                agescales[pos][0]), _('ago'))
        pos += 1

    return _(u'just now')


def credentials_hidder(uri):
    """
    Removes user:password from given url string
    
    :param uri:
    :rtype: unicode
    :returns: filtered list of strings    
    """
    if not uri:
        return ''

    proto = ''

    for pat in ('https://', 'http://'):
        if uri.startswith(pat):
            uri = uri[len(pat):]
            proto = pat
            break

    # remove passwords and username
    uri = uri[uri.find('@') + 1:]

    # get the port
    cred_pos = uri.find(':')
    if cred_pos == -1:
        host, port = uri, None
    else:
        host, port = uri[:cred_pos], uri[cred_pos + 1:]

    return filter(None, [proto, host, port])
