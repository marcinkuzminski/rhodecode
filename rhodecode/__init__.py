# -*- coding: utf-8 -*-
"""
    rhodecode.__init__
    ~~~~~~~~~~~~~~~~~~

    RhodeCode, a web based repository management based on pylons
    versioning implementation: http://semver.org/

    :created_on: Apr 9, 2010
    :author: marcink
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>    
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


VERSION = (1, 1, 2)
__version__ = '.'.join((str(each) for each in VERSION[:4]))
__dbversion__ = 2 #defines current db version for migrations

try:
    from rhodecode.lib.utils import get_current_revision
    _rev = get_current_revision()
except ImportError:
    #this is needed when doing some setup.py operations
    _rev = False

if len(VERSION) > 3 and _rev:
    __version__ += ' [rev:%s]' % _rev[0]

def get_version():
    """Returns shorter version (digit parts only) as string."""

    return '.'.join((str(each) for each in VERSION[:3]))

BACKENDS = {
    'hg': 'Mercurial repository',
   #'git': 'Git repository',
}
