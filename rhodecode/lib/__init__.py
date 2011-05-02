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

#Additional mappings that are not present in the pygments lexers
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
    file based sqlite databases. This prevents errors on sqlite.
    
    """
    from sqlalchemy import engine_from_config as efc
    from sqlalchemy.pool import NullPool

    url = configuration[prefix + 'url']

    if url.startswith('sqlite'):
        kwargs.update({'poolclass':NullPool})

    return efc(configuration, prefix, **kwargs)


