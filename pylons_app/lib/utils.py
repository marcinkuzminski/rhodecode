#!/usr/bin/env python
# encoding: utf-8
# Utilities for hg app
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
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
import shutil

"""
Created on April 18, 2010
Utilities for hg app
@author: marcink
"""
from beaker.cache import cache_region
from mercurial import ui, config, hg
from mercurial.error import RepoError
from pylons_app.model import meta
from pylons_app.model.db import Repository, User, HgAppUi, HgAppSettings
from vcs.backends.base import BaseChangeset
from vcs.utils.lazy import LazyProperty
import logging
import os
from os.path import dirname as dn, join as jn
import tarfile
log = logging.getLogger(__name__)


def get_repo_slug(request):
    return request.environ['pylons.routes_dict'].get('repo_name')

def is_mercurial(environ):
    """
    Returns True if request's target is mercurial server - header
    ``HTTP_ACCEPT`` of such request would start with ``application/mercurial``.
    """
    http_accept = environ.get('HTTP_ACCEPT')
    if http_accept and http_accept.startswith('application/mercurial'):
        return True
    return False

def check_repo_dir(paths):
    repos_path = paths[0][1].split('/')
    if repos_path[-1] in ['*', '**']:
        repos_path = repos_path[:-1]
    if repos_path[0] != '/':
        repos_path[0] = '/'
    if not os.path.isdir(os.path.join(*repos_path)):
        raise Exception('Not a valid repository in %s' % paths[0][1])

def check_repo_fast(repo_name, base_path):
    if os.path.isdir(os.path.join(base_path, repo_name)):return False
    return True

def check_repo(repo_name, base_path, verify=True):

    repo_path = os.path.join(base_path, repo_name)

    try:
        if not check_repo_fast(repo_name, base_path):
            return False
        r = hg.repository(ui.ui(), repo_path)
        if verify:
            hg.verify(r)
        #here we hnow that repo exists it was verified
        log.info('%s repo is already created', repo_name)
        return False
    except RepoError:
        #it means that there is no valid repo there...
        log.info('%s repo is free for creation', repo_name)
        return True

def ask_ok(prompt, retries=4, complaint='Yes or no, please!'):
    while True:
        ok = raw_input(prompt)
        if ok in ('y', 'ye', 'yes'): return True
        if ok in ('n', 'no', 'nop', 'nope'): return False
        retries = retries - 1
        if retries < 0: raise IOError
        print complaint
        
@cache_region('super_short_term', 'cached_hg_ui')
def get_hg_ui_cached():
    try:
        sa = meta.Session
        ret = sa.query(HgAppUi).all()
    finally:
        meta.Session.remove()
    return ret


def get_hg_settings():
    try:
        sa = meta.Session
        ret = sa.query(HgAppSettings).all()
    finally:
        meta.Session.remove()
        
    if not ret:
        raise Exception('Could not get application settings !')
    settings = {}
    for each in ret:
        settings['hg_app_' + each.app_settings_name] = each.app_settings_value    
    
    return settings

def get_hg_ui_settings():
    try:
        sa = meta.Session
        ret = sa.query(HgAppUi).all()
    finally:
        meta.Session.remove()
        
    if not ret:
        raise Exception('Could not get application ui settings !')
    settings = {}
    for each in ret:
        k = each.ui_key
        v = each.ui_value
        if k == '/':
            k = 'root_path'
        
        if k.find('.') != -1:
            k = k.replace('.', '_')
        
        if each.ui_section == 'hooks':
            v = each.ui_active
        
        settings[each.ui_section + '_' + k] = v  
    
    return settings

#propagated from mercurial documentation
ui_sections = ['alias', 'auth',
                'decode/encode', 'defaults',
                'diff', 'email',
                'extensions', 'format',
                'merge-patterns', 'merge-tools',
                'hooks', 'http_proxy',
                'smtp', 'patch',
                'paths', 'profiling',
                'server', 'trusted',
                'ui', 'web', ]
        
def make_ui(read_from='file', path=None, checkpaths=True):        
    """
    A function that will read python rc files or database
    and make an mercurial ui object from read options
    
    @param path: path to mercurial config file
    @param checkpaths: check the path
    @param read_from: read from 'file' or 'db'
    """

    baseui = ui.ui()

    if read_from == 'file':
        if not os.path.isfile(path):
            log.warning('Unable to read config file %s' % path)
            return False
        log.debug('reading hgrc from %s', path)
        cfg = config.config()
        cfg.read(path)
        for section in ui_sections:
            for k, v in cfg.items(section):
                baseui.setconfig(section, k, v)
                log.debug('settings ui from file[%s]%s:%s', section, k, v)
        if checkpaths:check_repo_dir(cfg.items('paths'))                
              
        
    elif read_from == 'db':
        hg_ui = get_hg_ui_cached()
        for ui_ in hg_ui:
            if ui_.ui_active:
                log.debug('settings ui from db[%s]%s:%s', ui_.ui_section, ui_.ui_key, ui_.ui_value)
                baseui.setconfig(ui_.ui_section, ui_.ui_key, ui_.ui_value)
        
    
    return baseui


def set_hg_app_config(config):
    hgsettings = get_hg_settings()
    
    for k, v in hgsettings.items():
        config[k] = v

def invalidate_cache(name, *args):
    """Invalidates given name cache"""
    
    from beaker.cache import region_invalidate
    log.info('INVALIDATING CACHE FOR %s', name)
    
    """propagate our arguments to make sure invalidation works. First
    argument has to be the name of cached func name give to cache decorator
    without that the invalidation would not work"""
    tmp = [name]
    tmp.extend(args)
    args = tuple(tmp)
    
    if name == 'cached_repo_list':
        from pylons_app.model.hg_model import _get_repos_cached
        region_invalidate(_get_repos_cached, None, *args)
        
    if name == 'full_changelog':
        from pylons_app.model.hg_model import _full_changelog_cached
        region_invalidate(_full_changelog_cached, None, *args)
        
class EmptyChangeset(BaseChangeset):
    
    revision = -1
    message = ''
    
    @LazyProperty
    def raw_id(self):
        """
        Returns raw string identifing this changeset, useful for web
        representation.
        """
        return '0' * 12


def repo2db_mapper(initial_repo_list, remove_obsolete=False):
    """
    maps all found repositories into db
    """
    from pylons_app.model.repo_model import RepoModel
    
    sa = meta.Session
    user = sa.query(User).filter(User.admin == True).first()
    
    rm = RepoModel()
    
    for name, repo in initial_repo_list.items():
        if not sa.query(Repository).filter(Repository.repo_name == name).scalar():
            log.info('repository %s not found creating default', name)
                
            form_data = {
                         'repo_name':name,
                         'description':repo.description if repo.description != 'unknown' else \
                                        'auto description for %s' % name,
                         'private':False
                         }
            rm.create(form_data, user, just_db=True)


    if remove_obsolete:
        #remove from database those repositories that are not in the filesystem
        for repo in sa.query(Repository).all():
            if repo.repo_name not in initial_repo_list.keys():
                sa.delete(repo)
                sa.commit()

    
    meta.Session.remove()

from UserDict import DictMixin

class OrderedDict(dict, DictMixin):

    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        try:
            self.__end
        except AttributeError:
            self.clear()
        self.update(*args, **kwds)

    def clear(self):
        self.__end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.__map = {}                 # key --> [key, prev, next]
        dict.clear(self)

    def __setitem__(self, key, value):
        if key not in self:
            end = self.__end
            curr = end[1]
            curr[2] = end[1] = self.__map[key] = [key, curr, end]
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        key, prev, next = self.__map.pop(key)
        prev[2] = next
        next[1] = prev

    def __iter__(self):
        end = self.__end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.__end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def popitem(self, last=True):
        if not self:
            raise KeyError('dictionary is empty')
        if last:
            key = reversed(self).next()
        else:
            key = iter(self).next()
        value = self.pop(key)
        return key, value

    def __reduce__(self):
        items = [[k, self[k]] for k in self]
        tmp = self.__map, self.__end
        del self.__map, self.__end
        inst_dict = vars(self).copy()
        self.__map, self.__end = tmp
        if inst_dict:
            return (self.__class__, (items,), inst_dict)
        return self.__class__, (items,)

    def keys(self):
        return list(self)

    setdefault = DictMixin.setdefault
    update = DictMixin.update
    pop = DictMixin.pop
    values = DictMixin.values
    items = DictMixin.items
    iterkeys = DictMixin.iterkeys
    itervalues = DictMixin.itervalues
    iteritems = DictMixin.iteritems

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, self.items())

    def copy(self):
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d

    def __eq__(self, other):
        if isinstance(other, OrderedDict):
            return len(self) == len(other) and self.items() == other.items()
        return dict.__eq__(self, other)

    def __ne__(self, other):
        return not self == other

def make_test_env():
    """Makes a fresh database from base64+zlib dump and 
    install test repository into tmp dir
    """
    new_db_dump = """
eJztXN1vE8sVn9nxR+wAIXDpFiiXjSAXfEOc2ElwQkVLPjYf5NNOAklUydrYG3tv1t5ldx0nuUJV\noL
cPrVr1X7jSfUJ96nMfK1Xty23VqlWlPlRIlahUXbXqFUL0pTNjx5614xAoKEDmJ3t2zpkzM2fO\neHe+
zno+PqU5qrRmWDnFkXqAB0AIbkkSAKANf8+BKprwFzI0G28ECXQ+PufFEYT+Tehz6L/oaSnK\nwcFxGP
igFQfHjuMg4CehH7UA9Af0Y2ShWdSPLmOSg+N9x7U9eKf9PiC2nIWm4mTtri4nZ3Z9DE/5\nfOD0+RZY
VFdXFVstWHoXPOPFvDbKU3TdKCbNgp39GLZ5MPtKW5WtWKmstqFmtqVtzZRWt6NQRFjk\ngkhESJ6kbe
trim6rcFTAdcfuwqxhrNuprJLPqBnLKJhhSzWNpK1tq+aWkzXyN8wt3cjbScU0w7q2\nGqbyVSHYAXE5
kSv15RTMtOKo2YxUikjf+SgKg4Dc/38C6Dn6Gn2FnqDH6K+Y5ODgeGfhRRD6/ST0\n+Ujo9ZLQ4yEhQi
QUBBJCeFy4BLywHaCfCEXM+AJHOWpx39sMrux4IbzQ3gMc1XaSlpop6IoVvRxV\nLke6L4/cmx7vjedG
4qmVmXvTW5nl7PDaSmFEXR6ejC+YVrpnsNi1fn17fHldj06p6YH84tzaGKBF\n5ZWcSq66Uorn8Iih5W
/ZBolqejhl5O57mkEPqf6sOFCq3lRsu2hYaayHrTplJeJD/Uu3p7u3Er19\nS4sb26PmemQiE54vLKfn
I8Wx2/Nd+XurmbH4TOpupHdk25I/sYbmCgDQstK0oHLdpWGmc1U3MqR6\nbICF123RHb/QDNpIm1rFnk
HaJiWd0/Llpgzq41lzIJMrjMXi2/JmdyGxMDKnjs1FR9WMcduMb3TZ\nfZuZTXVs1uiS53NxY9yan4Vw
PDNICqEl3dKNlKJnDdshbYh2R7o7uwc6I1EpGr3RHbvREwn3D/T3\nd/fuBFAzaHdpUu7csi6Tw4ou94
zOLt3JxTNZo7g8muvV1Lg6sNj/SX4dD7srqenpfCJ6d3g5vKRM\njq/Ob3VHIXgJXaKx8PWBvoHrvfdg
MzhPVDl/vgek1TWloO927tbUdsqeNzfurK5Frq+v5NbHZ1bG\nCnZxdnxxbGStmOudnwub6+rQYNxZku
Wh28Ph9Nos2C3EfblVvhJlyPjvRY+Z8f91dzUHB8fhYf/x\nv3T/PwL47v87+iX6I45ycHC8dWhFV6Br
7ukVUQ/cYzroOYnaXZLoBGqD1TmW0IzOw/IUAJL9v6Dg\nA+jP6Ofo+yiBelFA+IvwC2EFMzmOCBJBD/
huMZsJ41+MZjuqFVYKjpFUUo62oThqosyV8mpRKtg4\nUtScrJTNdCqmSeNGwZFIFqmcRTPydwIeMPwp
W2ZOyRcU/SVLLWViym1v8oDOLrbcvJGvFpbWbGVV\nV9NhvweEZCyWslRcWVnINGzNMawtiXJxaRX5kM
8D+rqq8lZFtjaX+i2vB1zoxKL0dhrPSHSmj6u3\nFCzV4cH6fbuavSTFFEJp3KCUatsdqEa4aGkOqyel
y8IhwQM6BhhhrE2akSVkWfQKxKJ9jGhN8/NG\nWZCM/0H0q5r9P/Q79FvM5ODgeOtBZvLBIAkDARI2Nb
3E/h/O7wdDAAzBj+Cy8IXwpfAc/eZlat9R\noF+8eBE+bHXIgzSbIQcTyYJWiQjDCXlwQZYWBoemZKnC
lq4GAwUtqaWliZkFeUxOSDOzC9LM4tTU\nNYmm2GqKPqEX5KWFMmtd3WLJDUUvqCyDjhKqNDQ7OyUPzh
DmXGJiejCxLE3Ky9JVWl2IsBdnJuKL\nMssZHpeHJymjXMjEjHS1+5oUCYWCoYjgE+WLEGj5tLpp39Px
MzlJhjtKJytNSkYqUfRgHPlFUYQ/\nMKhZyPhm08DjMgdlUVPgSENj4DSyN1hp6u6Er8Kob3hplGEYrg
J2dxsrDLrZ6EpO6kYGlzCCdV2Y\nmJbrjVlS2G1Ohlc2aJ012TSqozuJLYpoiK0f8vjEm2Ij61MLJiP0
4g15XywapRffzpTPL166BB8k\naQeZqpXTbBv/4Gwm6nd1FpNAuqxKNuo4RsLdf1W+buQzrjSXkV1VuO
zjTgmG+vw+ceJSo5Yzmicj\nDNFE7n8BfQnQ33DAwcHxLqMFLxHEs47mkIGYrKM+xAsBMYZXBnquvLDC
D4Wsmne0FF3/kPm/gL6m\n8//DVp6Dg+PNo3b+7wOPAHgEH8F/CFfRT9GvD1u/vbFzv8kvdnTAhxF2nW
GrjqPlM3YNGdxrzbGb\nSOZuLN1o9uaScc3RXCnuVYhr+lZTi2sCd+C08iz4ZsAnxjtesAapZIrUMJpv
Bl8me7SGcfxBqtkv\ntrfDzwLU+pWdJU212fgJl93ZFGJ06qPWwNg0rWLkuuVPwxm2RfcS2YVOWrVTlm
a61o6uXimr4bJ4\npfp67r6So7MJeWJshhRcWf1ICXlUTsgzw/L87vpuj4XRrubsOjN2zCdOtjfqJNac
yQhLtcSOHzhj\nlKVOlsb/fwL0FAccHBzvLQJIhHRpIJAYXRPQ8R+i3wP84eDgeNfRCX3gAoRjGyk7Sc
78BUDPZdlJ\n0ZphSbvJZPyH6D8Afzg4ON5/HEMX4O7tD0v3/3OAPxwcHEcG1f0/hJ4A9Az9C184ODje
Q/gQ+WcP\nKPgEevX5IL0GyPiP0Fdl/7/D1pKDg+PNYe/3f+j4/wSP/88OWz8ODo43Ab+H3O0CKl19Qu
kaoPN/\nD/gcgM+FD4W7ws8OW886PNg+UTp4jlX8aJOOQR0a2XhrnVftbkrFubZM7+dkewA/zgYS9a6x
1erq\nXWRr0thDZLdfJ3uU7PI+rXcMfYWT6Bq33WtSrVNprGW/Y2VXUyIsdSp28sAZoyx1+kGulXqTfx
aq\ndrduZOxK5Ex9RxN2pZcx8So9XEozKw4D1Vdn6v0RFLdfeolM0r/U2d9buqRbvekZ/iv0IpulqrYr
\nl9sRo+rBEAyR+x8/ADg4OI4gyPyf3/8cHEcTJf+fpwB/ODg4jgSaoBfQ/QB+/s/BcSRR3f+H6Bng\n
e/8cHEcHpf1/CI+jHwEP3AToLtx8e9/9e//w8Hun6bHGDz+tvE+3uwfOxsW69+nYYw2WfjPHGtX9\n5A
MdfNQo9P+eS7youNdyVuJq4ot2zRsdnLgLCYYip/b7w5jKqUX51IREv4F/FJ7YBy96ja963sJS\n34yd
OXDGKEud/R8efZUt\n
"""    
    newdb = open('test.db','wb')
    newdb.write(new_db_dump.decode('base64').decode('zlib'))
    newdb.close()
    
    
    #PART TWO make test repo
    if os.path.isdir('/tmp/vcs_test'):
        shutil.rmtree('/tmp/vcs_test')
        
    cur_dir = dn(dn(os.path.abspath(__file__)))
    tar = tarfile.open(jn(cur_dir,'tests',"vcs_test.tar.gz"))
    tar.extractall('/tmp')
    tar.close()
    
    
    