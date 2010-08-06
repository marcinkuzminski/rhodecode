#!/usr/bin/env python
# encoding: utf-8
# custom hooks for application
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
#
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
"""
Created on Aug 6, 2010

@author: marcink
"""

import sys
import os
from pylons_app.lib import helpers as h

def repo_size(ui, repo, hooktype=None, **kwargs):

    if hooktype != 'changegroup':
        return False
    
    size_hg, size_root = 0, 0
    for path, dirs, files in os.walk(repo.root):
        if path.find('.hg') != -1:
            for f in files:
                size_hg += os.path.getsize(os.path.join(path, f))
        else:
            for f in files:
                size_root += os.path.getsize(os.path.join(path, f))
                
    size_hg_f = h.format_byte_size(size_hg)
    size_root_f = h.format_byte_size(size_root)
    size_total_f = h.format_byte_size(size_root + size_hg)                            
    sys.stdout.write('Repository size .hg:%s repo:%s total:%s\n' \
                     % (size_hg_f, size_root_f, size_total_f))
