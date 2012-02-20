# -*- coding: utf-8 -*-
"""
    rhodecode.lib.indexers.daemon
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A daemon will read from task table and run tasks

    :created_on: Jan 26, 2010
    :author: marcink
    :copyright: (C) 2010-2012 Marcin Kuzminski <marcin@python-works.com>
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
import sys
import logging
import traceback

from shutil import rmtree
from time import mktime

from os.path import dirname as dn
from os.path import join as jn

#to get the rhodecode import
project_path = dn(dn(dn(dn(os.path.realpath(__file__)))))
sys.path.append(project_path)


from rhodecode.model.scm import ScmModel
from rhodecode.lib import safe_unicode
from rhodecode.lib.indexers import INDEX_EXTENSIONS, SCHEMA, IDX_NAME

from rhodecode.lib.vcs.exceptions import ChangesetError, RepositoryError, \
    NodeDoesNotExistError

from whoosh.index import create_in, open_dir


log = logging.getLogger('whooshIndexer')
# create logger
log.setLevel(logging.DEBUG)
log.propagate = False
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s -"
                              " %(levelname)s - %(message)s")

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
log.addHandler(ch)


class WhooshIndexingDaemon(object):
    """
    Daemon for atomic jobs
    """

    def __init__(self, indexname=IDX_NAME, index_location=None,
                 repo_location=None, sa=None, repo_list=None):
        self.indexname = indexname

        self.index_location = index_location
        if not index_location:
            raise Exception('You have to provide index location')

        self.repo_location = repo_location
        if not repo_location:
            raise Exception('You have to provide repositories location')

        self.repo_paths = ScmModel(sa).repo_scan(self.repo_location)

        if repo_list:
            filtered_repo_paths = {}
            for repo_name, repo in self.repo_paths.items():
                if repo_name in repo_list:
                    filtered_repo_paths[repo_name] = repo

            self.repo_paths = filtered_repo_paths

        self.initial = False
        if not os.path.isdir(self.index_location):
            os.makedirs(self.index_location)
            log.info('Cannot run incremental index since it does not'
                     ' yet exist running full build')
            self.initial = True

    def get_paths(self, repo):
        """recursive walk in root dir and return a set of all path in that dir
        based on repository walk function
        """
        index_paths_ = set()
        try:
            tip = repo.get_changeset('tip')
            for topnode, dirs, files in tip.walk('/'):
                for f in files:
                    index_paths_.add(jn(repo.path, f.path))

        except RepositoryError, e:
            log.debug(traceback.format_exc())
            pass
        return index_paths_

    def get_node(self, repo, path):
        n_path = path[len(repo.path) + 1:]
        node = repo.get_changeset().get_node(n_path)
        return node

    def get_node_mtime(self, node):
        return mktime(node.last_changeset.date.timetuple())

    def add_doc(self, writer, path, repo, repo_name):
        """Adding doc to writer this function itself fetches data from
        the instance of vcs backend"""
        node = self.get_node(repo, path)

        #we just index the content of chosen files, and skip binary files
        if node.extension in INDEX_EXTENSIONS and not node.is_binary:

            u_content = node.content
            if not isinstance(u_content, unicode):
                log.warning('  >> %s Could not get this content as unicode '
                          'replacing with empty content', path)
                u_content = u''
            else:
                log.debug('    >> %s [WITH CONTENT]' % path)

        else:
            log.debug('    >> %s' % path)
            #just index file name without it's content
            u_content = u''

        writer.add_document(owner=unicode(repo.contact),
                        repository=safe_unicode(repo_name),
                        path=safe_unicode(path),
                        content=u_content,
                        modtime=self.get_node_mtime(node),
                        extension=node.extension)

    def build_index(self):
        if os.path.exists(self.index_location):
            log.debug('removing previous index')
            rmtree(self.index_location)

        if not os.path.exists(self.index_location):
            os.mkdir(self.index_location)

        idx = create_in(self.index_location, SCHEMA, indexname=IDX_NAME)
        writer = idx.writer()

        for repo_name, repo in self.repo_paths.items():
            log.debug('building index @ %s' % repo.path)

            for idx_path in self.get_paths(repo):
                self.add_doc(writer, idx_path, repo, repo_name)

        log.debug('>> COMMITING CHANGES <<')
        writer.commit(merge=True)
        log.debug('>>> FINISHED BUILDING INDEX <<<')

    def update_index(self):
        log.debug('STARTING INCREMENTAL INDEXING UPDATE')

        idx = open_dir(self.index_location, indexname=self.indexname)
        # The set of all paths in the index
        indexed_paths = set()
        # The set of all paths we need to re-index
        to_index = set()

        reader = idx.reader()
        writer = idx.writer()

        # Loop over the stored fields in the index
        for fields in reader.all_stored_fields():
            indexed_path = fields['path']
            indexed_paths.add(indexed_path)

            repo = self.repo_paths[fields['repository']]

            try:
                node = self.get_node(repo, indexed_path)
            except (ChangesetError, NodeDoesNotExistError):
                # This file was deleted since it was indexed
                log.debug('removing from index %s' % indexed_path)
                writer.delete_by_term('path', indexed_path)

            else:
                # Check if this file was changed since it was indexed
                indexed_time = fields['modtime']
                mtime = self.get_node_mtime(node)
                if mtime > indexed_time:
                    # The file has changed, delete it and add it to the list of
                    # files to reindex
                    log.debug('adding to reindex list %s' % indexed_path)
                    writer.delete_by_term('path', indexed_path)
                    to_index.add(indexed_path)

        # Loop over the files in the filesystem
        # Assume we have a function that gathers the filenames of the
        # documents to be indexed
        for repo_name, repo in self.repo_paths.items():
            for path in self.get_paths(repo):
                if path in to_index or path not in indexed_paths:
                    # This is either a file that's changed, or a new file
                    # that wasn't indexed before. So index it!
                    self.add_doc(writer, path, repo, repo_name)
                    log.debug('re indexing %s' % path)

        log.debug('>> COMMITING CHANGES <<')
        writer.commit(merge=True)
        log.debug('>>> FINISHED REBUILDING INDEX <<<')

    def run(self, full_index=False):
        """Run daemon"""
        if full_index or self.initial:
            self.build_index()
        else:
            self.update_index()
