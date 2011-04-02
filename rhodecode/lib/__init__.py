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
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your opinion) any later version of the license.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.

def str2bool(s):
    if s is None:
        return False
    if s in (True, False):
        return s
    s = str(s).strip().lower()
    return s in ('t', 'true', 'y', 'yes', 'on', '1')

def generate_api_key(username, salt=None):
    """
    Generates uniq API key for given username
    
    :param username: username as string
    :param salt: salt to hash generate KEY
    """
    from tempfile import _RandomNameSequence
    import hashlib

    if salt is None:
        salt = _RandomNameSequence().next()

    return hashlib.sha1(username + salt).hexdigest()

def safe_unicode(_str):
    """
    safe unicode function. In case of UnicodeDecode error we try to return
    unicode with errors replace, if this fails we return unicode with 
    string_escape decoding 
    """

    if isinstance(_str, unicode):
        return _str

    try:
        u_str = unicode(_str)
    except UnicodeDecodeError:
        try:
            u_str = _str.decode('utf-8', 'replace')
        except UnicodeDecodeError:
            #incase we have a decode error just represent as byte string
            u_str = unicode(_str.encode('string_escape'))

    return u_str
