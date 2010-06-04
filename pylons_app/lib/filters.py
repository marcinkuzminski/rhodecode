#!/usr/bin/env python
# encoding: utf-8
# simple filters for hg apps html templates
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

"""
Created on April 12, 2010
simple filters for hg apps html templates
@author: marcink
"""

from mercurial import util
from mercurial.templatefilters import age as _age, person as _person
from string import punctuation

def clean_repo(repo_name):
    for x in punctuation:
        if x != '_':
            repo_name = repo_name.replace(x, '')
    repo_name = repo_name.lower().strip()
    return repo_name.replace(' ', '_')

age = lambda  x:_age(x)
capitalize = lambda x: x.capitalize()
date = lambda x: util.datestr(x)
email = util.email
person = lambda x: _person(x)
hgdate = lambda  x: "%d %d" % x
isodate = lambda  x: util.datestr(x, '%Y-%m-%d %H:%M %1%2')
isodatesec = lambda  x: util.datestr(x, '%Y-%m-%d %H:%M:%S %1%2')
localdate = lambda  x: (x[0], util.makedate()[1])
rfc822date = lambda  x: util.datestr(x, "%a, %d %b %Y %H:%M:%S %1%2")
rfc3339date = lambda  x: util.datestr(x, "%Y-%m-%dT%H:%M:%S%1:%2")
time_ago = lambda x: util.datestr(_age(x), "%a, %d %b %Y %H:%M:%S %1%2")
