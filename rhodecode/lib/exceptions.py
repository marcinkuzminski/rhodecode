#!/usr/bin/env python
# encoding: utf-8
# Custom Exceptions modules
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
#
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
"""
Created on Nov 17, 2010
Custom Exceptions modules
@author: marcink
"""

class LdapUsernameError(Exception):pass
class LdapPasswordError(Exception):pass
class LdapConnectionError(Exception):pass
class LdapImportError(Exception):pass

class DefaultUserException(Exception):pass
class UserOwnsReposException(Exception):pass
