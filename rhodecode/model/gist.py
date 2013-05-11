# -*- coding: utf-8 -*-
"""
    rhodecode.model.gist
    ~~~~~~~~~~~~~~~~~~~~

    gist model for RhodeCode

    :created_on: May 9, 2013
    :author: marcink
    :copyright: (C) 2011-2013 Marcin Kuzminski <marcin@python-works.com>
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
from __future__ import with_statement
import os
import time
import logging
import traceback
import shutil

from pylons.i18n.translation import _
from rhodecode.lib.utils2 import safe_unicode, unique_id, safe_int, \
    time_to_datetime, safe_str, AttributeDict
from rhodecode.lib.compat import json
from rhodecode.lib import helpers as h
from rhodecode.model import BaseModel
from rhodecode.model.db import Gist
from rhodecode.model.repo import RepoModel
from rhodecode.model.scm import ScmModel

log = logging.getLogger(__name__)

GIST_STORE_LOC = '.rc_gist_store'
GIST_METADATA_FILE = '.rc_gist_metadata'


class GistModel(BaseModel):

    def _get_gist(self, gist):
        """
        Helper method to get gist by ID, or gist_access_id as a fallback

        :param gist: GistID, gist_access_id, or Gist instance
        """
        return self._get_instance(Gist, gist,
                                  callback=Gist.get_by_access_id)

    def __delete_gist(self, gist):
        """
        removes gist from filesystem

        :param gist: gist object
        """
        root_path = RepoModel().repos_path
        rm_path = os.path.join(root_path, GIST_STORE_LOC, gist.gist_access_id)
        log.info("Removing %s" % (rm_path))
        shutil.rmtree(rm_path)

    def get_gist(self, gist):
        return self._get_gist(gist)

    def get_gist_files(self, gist_access_id):
        """
        Get files for given gist

        :param gist_access_id:
        """
        repo = Gist.get_by_access_id(gist_access_id)
        cs = repo.scm_instance.get_changeset()
        return (
         cs, [n for n in cs.get_node('/')]
        )

    def create(self, description, owner, gist_mapping,
               gist_type=Gist.GIST_PUBLIC, lifetime=-1):
        """

        :param description: description of the gist
        :param owner: user who created this gist
        :param gist_mapping: mapping {filename:{'content':content},...}
        :param gist_type: type of gist private/public
        :param lifetime: in minutes, -1 == forever
        """
        gist_id = safe_unicode(unique_id(20))
        lifetime = safe_int(lifetime, -1)
        gist_expires = time.time() + (lifetime * 60) if lifetime != -1 else -1
        log.debug('set GIST expiration date to: %s'
                  % (time_to_datetime(gist_expires)
                   if gist_expires != -1 else 'forever'))
        #create the Database version
        gist = Gist()
        gist.gist_description = description
        gist.gist_access_id = gist_id
        gist.gist_owner = owner.user_id
        gist.gist_expires = gist_expires
        gist.gist_type = safe_unicode(gist_type)
        self.sa.add(gist)
        self.sa.flush()
        if gist_type == Gist.GIST_PUBLIC:
            # use DB ID for easy to use GIST ID
            gist_id = safe_unicode(gist.gist_id)
            gist.gist_access_id = gist_id
            self.sa.add(gist)

        gist_repo_path = os.path.join(GIST_STORE_LOC, gist_id)
        log.debug('Creating new %s GIST repo in %s' % (gist_type, gist_repo_path))
        repo = RepoModel()._create_repo(repo_name=gist_repo_path, alias='hg',
                                        parent=None)

        processed_mapping = {}
        for filename in gist_mapping:
            if filename != os.path.basename(filename):
                raise Exception('Filename cannot be inside a directory')

            content = gist_mapping[filename]['content']
            #TODO: expand support for setting explicit lexers
#             if lexer is None:
#                 try:
#                     lexer = pygments.lexers.guess_lexer_for_filename(filename,content)
#                 except pygments.util.ClassNotFound:
#                     lexer = 'text'
            processed_mapping[filename] = {'content': content}

        # now create single multifile commit
        message = 'added file'
        message += 's: ' if len(processed_mapping) > 1 else ': '
        message += ', '.join([x for x in processed_mapping])

        #fake RhodeCode Repository object
        fake_repo = AttributeDict(dict(
            repo_name=gist_repo_path,
            scm_instance_no_cache=lambda: repo,
        ))
        ScmModel().create_nodes(
            user=owner.user_id, repo=fake_repo,
            message=message,
            nodes=processed_mapping,
            trigger_push_hook=False
        )
        # store metadata inside the gist, this can be later used for imports
        # or gist identification
        metadata = {
            'gist_db_id': gist.gist_id,
            'gist_access_id': gist.gist_access_id,
            'gist_owner_id': owner.user_id,
            'gist_type': gist.gist_type,
            'gist_exipres': gist.gist_expires
        }
        with open(os.path.join(repo.path, '.hg', GIST_METADATA_FILE), 'wb') as f:
            f.write(json.dumps(metadata))
        return gist

    def delete(self, gist, fs_remove=True):
        gist = self._get_gist(gist)

        try:
            self.sa.delete(gist)
            if fs_remove:
                self.__delete_gist(gist)
            else:
                log.debug('skipping removal from filesystem')

        except Exception:
            log.error(traceback.format_exc())
            raise
