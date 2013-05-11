# -*- coding: utf-8 -*-
"""
    rhodecode.lib.utils
    ~~~~~~~~~~~~~~~~~~~

    Some simple helper functions

    :created_on: Jan 5, 2011
    :author: marcink
    :copyright: (C) 2011-2012 Marcin Kuzminski <marcin@python-works.com>
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

import os
import re
import sys
import time
import uuid
import datetime
import traceback
import webob

from pylons.i18n.translation import _, ungettext
from rhodecode.lib.vcs.utils.lazy import LazyProperty
from rhodecode.lib.compat import json


def __get_lem():
    """
    Get language extension map based on what's inside pygments lexers
    """
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


def aslist(obj, sep=None, strip=True):
    """
    Returns given string separated by sep as list

    :param obj:
    :param sep:
    :param strip:
    """
    if isinstance(obj, (basestring)):
        lst = obj.split(sep)
        if strip:
            lst = [v.strip() for v in lst]
        return lst
    elif isinstance(obj, (list, tuple)):
        return obj
    elif obj is None:
        return []
    else:
        return [obj]


def convert_line_endings(line, mode):
    """
    Converts a given line  "line end" accordingly to given mode

    Available modes are::
        0 - Unix
        1 - Mac
        2 - DOS

    :param line: given line to convert
    :param mode: mode to convert to
    :rtype: str
    :return: converted line according to mode
    """
    from string import replace

    if mode == 0:
            line = replace(line, '\r\n', '\n')
            line = replace(line, '\r', '\n')
    elif mode == 1:
            line = replace(line, '\r\n', '\r')
            line = replace(line, '\n', '\r')
    elif mode == 2:
            line = re.sub("\r(?!\n)|(?<!\r)\n", "\r\n", line)
    return line


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
    Generates unique API key for given username, if salt is not given
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


def safe_int(val, default=None):
    """
    Returns int() of val if val is not convertable to int use default
    instead

    :param val:
    :param default:
    """

    try:
        val = int(val)
    except (ValueError, TypeError):
        val = default

    return val


def safe_unicode(str_, from_encoding=None):
    """
    safe unicode function. Does few trick to turn str_ into unicode

    In case of UnicodeDecode error we try to return it with encoding detected
    by chardet library if it fails fallback to unicode with errors replaced

    :param str_: string to decode
    :rtype: unicode
    :returns: unicode object
    """
    if isinstance(str_, unicode):
        return str_

    if not from_encoding:
        import rhodecode
        DEFAULT_ENCODINGS = aslist(rhodecode.CONFIG.get('default_encoding',
                                                        'utf8'), sep=',')
        from_encoding = DEFAULT_ENCODINGS

    if not isinstance(from_encoding, (list, tuple)):
        from_encoding = [from_encoding]

    try:
        return unicode(str_)
    except UnicodeDecodeError:
        pass

    for enc in from_encoding:
        try:
            return unicode(str_, enc)
        except UnicodeDecodeError:
            pass

    try:
        import chardet
        encoding = chardet.detect(str_)['encoding']
        if encoding is None:
            raise Exception()
        return str_.decode(encoding)
    except (ImportError, UnicodeDecodeError, Exception):
        return unicode(str_, from_encoding[0], 'replace')


def safe_str(unicode_, to_encoding=None):
    """
    safe str function. Does few trick to turn unicode_ into string

    In case of UnicodeEncodeError we try to return it with encoding detected
    by chardet library if it fails fallback to string with errors replaced

    :param unicode_: unicode to encode
    :rtype: str
    :returns: str object
    """

    # if it's not basestr cast to str
    if not isinstance(unicode_, basestring):
        return str(unicode_)

    if isinstance(unicode_, str):
        return unicode_

    if not to_encoding:
        import rhodecode
        DEFAULT_ENCODINGS = aslist(rhodecode.CONFIG.get('default_encoding',
                                                        'utf8'), sep=',')
        to_encoding = DEFAULT_ENCODINGS

    if not isinstance(to_encoding, (list, tuple)):
        to_encoding = [to_encoding]

    for enc in to_encoding:
        try:
            return unicode_.encode(enc)
        except UnicodeEncodeError:
            pass

    try:
        import chardet
        encoding = chardet.detect(unicode_)['encoding']
        if encoding is None:
            raise UnicodeEncodeError()

        return unicode_.encode(encoding)
    except (ImportError, UnicodeEncodeError):
        return unicode_.encode(to_encoding[0], 'replace')

    return safe_str


def remove_suffix(s, suffix):
    if s.endswith(suffix):
        s = s[:-1 * len(suffix)]
    return s


def remove_prefix(s, prefix):
    if s.startswith(prefix):
        s = s[len(prefix):]
    return s


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

        log = logging.getLogger('sqlalchemy.engine')
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


def age(prevdate, show_short_version=False, now=None):
    """
    turns a datetime into an age string.
    If show_short_version is True, then it will generate a not so accurate but shorter string,
    example: 2days ago, instead of 2 days and 23 hours ago.

    :param prevdate: datetime object
    :param show_short_version: if it should aproximate the date and return a shorter string
    :rtype: unicode
    :returns: unicode words describing age
    """
    now = now or datetime.datetime.now()
    order = ['year', 'month', 'day', 'hour', 'minute', 'second']
    deltas = {}
    future = False

    if prevdate > now:
        now, prevdate = prevdate, now
        future = True
    if future:
        prevdate = prevdate.replace(microsecond=0)
    # Get date parts deltas
    from dateutil import relativedelta
    for part in order:
        d = relativedelta.relativedelta(now, prevdate)
        deltas[part] = getattr(d, part + 's')

    # Fix negative offsets (there is 1 second between 10:59:59 and 11:00:00,
    # not 1 hour, -59 minutes and -59 seconds)
    for num, length in [(5, 60), (4, 60), (3, 24)]:  # seconds, minutes, hours
        part = order[num]
        carry_part = order[num - 1]

        if deltas[part] < 0:
            deltas[part] += length
            deltas[carry_part] -= 1

    # Same thing for days except that the increment depends on the (variable)
    # number of days in the month
    month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if deltas['day'] < 0:
        if prevdate.month == 2 and (prevdate.year % 4 == 0 and
            (prevdate.year % 100 != 0 or prevdate.year % 400 == 0)):
            deltas['day'] += 29
        else:
            deltas['day'] += month_lengths[prevdate.month - 1]

        deltas['month'] -= 1

    if deltas['month'] < 0:
        deltas['month'] += 12
        deltas['year'] -= 1

    # Format the result
    fmt_funcs = {
        'year': lambda d: ungettext(u'%d year', '%d years', d) % d,
        'month': lambda d: ungettext(u'%d month', '%d months', d) % d,
        'day': lambda d: ungettext(u'%d day', '%d days', d) % d,
        'hour': lambda d: ungettext(u'%d hour', '%d hours', d) % d,
        'minute': lambda d: ungettext(u'%d minute', '%d minutes', d) % d,
        'second': lambda d: ungettext(u'%d second', '%d seconds', d) % d,
    }

    for i, part in enumerate(order):
        value = deltas[part]
        if value == 0:
            continue

        if i < 5:
            sub_part = order[i + 1]
            sub_value = deltas[sub_part]
        else:
            sub_value = 0

        if sub_value == 0 or show_short_version:
            if future:
                return _(u'in %s') % fmt_funcs[part](value)
            else:
                return _(u'%s ago') % fmt_funcs[part](value)
        if future:
            return _(u'in %s and %s') % (fmt_funcs[part](value),
                fmt_funcs[sub_part](sub_value))
        else:
            return _(u'%s and %s ago') % (fmt_funcs[part](value),
                fmt_funcs[sub_part](sub_value))

    return _(u'just now')


def uri_filter(uri):
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


def credentials_filter(uri):
    """
    Returns a url with removed credentials

    :param uri:
    """

    uri = uri_filter(uri)
    #check if we have port
    if len(uri) > 2 and uri[2]:
        uri[2] = ':' + uri[2]

    return ''.join(uri)


def get_changeset_safe(repo, rev):
    """
    Safe version of get_changeset if this changeset doesn't exists for a
    repo it returns a Dummy one instead

    :param repo:
    :param rev:
    """
    from rhodecode.lib.vcs.backends.base import BaseRepository
    from rhodecode.lib.vcs.exceptions import RepositoryError
    from rhodecode.lib.vcs.backends.base import EmptyChangeset
    if not isinstance(repo, BaseRepository):
        raise Exception('You must pass an Repository '
                        'object as first argument got %s', type(repo))

    try:
        cs = repo.get_changeset(rev)
    except RepositoryError:
        cs = EmptyChangeset(requested_revision=rev)
    return cs


def datetime_to_time(dt):
    if dt:
        return time.mktime(dt.timetuple())


def time_to_datetime(tm):
    if tm:
        if isinstance(tm, basestring):
            try:
                tm = float(tm)
            except ValueError:
                return
        return datetime.datetime.fromtimestamp(tm)

MENTIONS_REGEX = r'(?:^@|\s@)([a-zA-Z0-9]{1}[a-zA-Z0-9\-\_\.]+)(?:\s{1})'


def extract_mentioned_users(s):
    """
    Returns unique usernames from given string s that have @mention

    :param s: string to get mentions
    """
    usrs = set()
    for username in re.findall(MENTIONS_REGEX, s):
        usrs.add(username)

    return sorted(list(usrs), key=lambda k: k.lower())


class AttributeDict(dict):
    def __getattr__(self, attr):
        return self.get(attr, None)
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def fix_PATH(os_=None):
    """
    Get current active python path, and append it to PATH variable to fix issues
    of subprocess calls and different python versions
    """
    if os_ is None:
        import os
    else:
        os = os_

    cur_path = os.path.split(sys.executable)[0]
    if not os.environ['PATH'].startswith(cur_path):
        os.environ['PATH'] = '%s:%s' % (cur_path, os.environ['PATH'])


def obfuscate_url_pw(engine):
    _url = engine or ''
    from sqlalchemy.engine import url as sa_url
    try:
        _url = sa_url.make_url(engine)
        if _url.password:
            _url.password = 'XXXXX'
    except Exception:
        pass
    return str(_url)


def get_server_url(environ):
    req = webob.Request(environ)
    return req.host_url + req.script_name


def _extract_extras(env=None):
    """
    Extracts the rc extras data from os.environ, and wraps it into named
    AttributeDict object
    """
    if not env:
        env = os.environ

    try:
        rc_extras = json.loads(env['RC_SCM_DATA'])
    except Exception:
        print os.environ
        print >> sys.stderr, traceback.format_exc()
        rc_extras = {}

    try:
        for k in ['username', 'repository', 'locked_by', 'scm', 'make_lock',
                  'action', 'ip']:
            rc_extras[k]
    except KeyError, e:
        raise Exception('Missing key %s in os.environ %s' % (e, rc_extras))

    return AttributeDict(rc_extras)


def _set_extras(extras):
    os.environ['RC_SCM_DATA'] = json.dumps(extras)


def unique_id(hexlen=32):
    alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjklmnpqrstuvwxyz"
    return suuid(truncate_to=hexlen, alphabet=alphabet)


def suuid(url=None, truncate_to=22, alphabet=None):
    """
    Generate and return a short URL safe UUID.

    If the url parameter is provided, set the namespace to the provided
    URL and generate a UUID.

    :param url to get the uuid for
    :truncate_to: truncate the basic 22 UUID to shorter version

    The IDs won't be universally unique any longer, but the probability of
    a collision will still be very low.
    """
    # Define our alphabet.
    _ALPHABET = alphabet or "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"

    # If no URL is given, generate a random UUID.
    if url is None:
        unique_id = uuid.uuid4().int
    else:
        unique_id = uuid.uuid3(uuid.NAMESPACE_URL, url).int

    alphabet_length = len(_ALPHABET)
    output = []
    while unique_id > 0:
        digit = unique_id % alphabet_length
        output.append(_ALPHABET[digit])
        unique_id = int(unique_id / alphabet_length)
    return "".join(output)[:truncate_to]
