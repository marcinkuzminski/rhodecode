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

from rhodecode.config.conf import INDEX_EXTENSIONS
from rhodecode.model.scm import ScmModel
from rhodecode.lib.utils2 import safe_unicode
from rhodecode.lib.indexers import SCHEMA, IDX_NAME, CHGSETS_SCHEMA, CHGSET_IDX_NAME

from rhodecode.lib.vcs.exceptions import ChangesetError, RepositoryError, \
    NodeDoesNotExistError

from whoosh.index import create_in, open_dir, exists_in
from whoosh.query import *
from whoosh.qparser import QueryParser

log = logging.getLogger('whoosh_indexer')


class WhooshIndexingDaemon(object):
    """
    Daemon for atomic indexing jobs
    """

    def __init__(self, indexname=IDX_NAME, index_location=None,
                 repo_location=None, sa=None, repo_list=None,
                 repo_update_list=None):
        self.indexname = indexname

        self.index_location = index_location
        if not index_location:
            raise Exception('You have to provide index location')

        self.repo_location = repo_location
        if not repo_location:
            raise Exception('You have to provide repositories location')

        self.repo_paths = ScmModel(sa).repo_scan(self.repo_location)

        #filter repo list
        if repo_list:
            self.filtered_repo_paths = {}
            for repo_name, repo in self.repo_paths.items():
                if repo_name in repo_list:
                    self.filtered_repo_paths[repo_name] = repo

            self.repo_paths = self.filtered_repo_paths

        #filter update repo list
        self.filtered_repo_update_paths = {}
        if repo_update_list:
            self.filtered_repo_update_paths = {}
            for repo_name, repo in self.repo_paths.items():
                if repo_name in repo_update_list:
                    self.filtered_repo_update_paths[repo_name] = repo
            self.repo_paths = self.filtered_repo_update_paths

        self.initial = True
        if not os.path.isdir(self.index_location):
            os.makedirs(self.index_location)
            log.info('Cannot run incremental index since it does not'
                     ' yet exist running full build')
        elif not exists_in(self.index_location, IDX_NAME):
            log.info('Running full index build as the file content'
                     ' index does not exist')
        elif not exists_in(self.index_location, CHGSET_IDX_NAME):
            log.info('Running full index build as the changeset'
                     ' index does not exist')
        else:
            self.initial = False

    def get_paths(self, repo):
        """
        recursive walk in root dir and return a set of all path in that dir
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
        """
        Adding doc to writer this function itself fetches data from
        the instance of vcs backend
        """

        node = self.get_node(repo, path)
        indexed = indexed_w_content = 0
        # we just index the content of chosen files, and skip binary files
        if node.extension in INDEX_EXTENSIONS and not node.is_binary:
            u_content = node.content
            if not isinstance(u_content, unicode):
                log.warning('  >> %s Could not get this content as unicode '
                            'replacing with empty content' % path)
                u_content = u''
            else:
                log.debug('    >> %s [WITH CONTENT]' % path)
                indexed_w_content += 1

        else:
            log.debug('    >> %s' % path)
            # just index file name without it's content
            u_content = u''
            indexed += 1

        p = safe_unicode(path)
        writer.add_document(
            fileid=p,
            owner=unicode(repo.contact),
            repository=safe_unicode(repo_name),
            path=p,
            content=u_content,
            modtime=self.get_node_mtime(node),
            extension=node.extension
        )
        return indexed, indexed_w_content

    def index_changesets(self, writer, repo_name, repo, start_rev=0):
        """
        Add all changeset in the vcs repo starting at start_rev
        to the index writer
        """

        log.debug('indexing changesets in %s[%d:]' % (repo_name, start_rev))

        indexed=0
        for cs in repo[start_rev:]:
            writer.add_document(
                path=unicode(cs.raw_id),
                owner=unicode(repo.contact),
                repository=safe_unicode(repo_name),
                author=cs.author,
                message=cs.message,
                revision=cs.revision,
                last=cs.last,
                added=u' '.join([node.path for node in cs.added]).lower(),
                removed=u' '.join([node.path for node in cs.removed]).lower(),
                changed=u' '.join([node.path for node in cs.changed]).lower(),
                parents=u' '.join([cs.raw_id for cs in cs.parents]),
            )
            indexed += 1

        log.debug('indexed %d changesets for repo %s' % (indexed, repo_name))

    def index_files(self, file_idx_writer, repo_name, repo):
        i_cnt = iwc_cnt = 0
        log.debug('building index for [%s]' % repo.path)
        for idx_path in self.get_paths(repo):
            i, iwc = self.add_doc(file_idx_writer, idx_path, repo, repo_name)
            i_cnt += i
            iwc_cnt += iwc

        log.debug('added %s files %s with content for repo %s' % (i_cnt + iwc_cnt, iwc_cnt, repo.path))

    def update_changeset_index(self):
        idx = open_dir(self.index_location, indexname=CHGSET_IDX_NAME)

        with idx.searcher() as searcher:
            writer = idx.writer()
            writer_is_dirty = False
            try:
                for repo_name, repo in self.repo_paths.items():
                    # skip indexing if there aren't any revs in the repo
                    revs = repo.revisions
                    if len(revs) < 1:
                        continue

                    qp = QueryParser('repository', schema=CHGSETS_SCHEMA)
                    q = qp.parse(u"last:t AND %s" % repo_name)

                    results = searcher.search(q, sortedby='revision')

                    last_rev = 0
                    if len(results) > 0:
                        last_rev = results[0]['revision']

                    # there are new changesets to index or a new repo to index
                    if last_rev == 0 or len(revs) > last_rev + 1:
                        # delete the docs in the index for the previous last changeset(s)
                        for hit in results:
                            q = qp.parse(u"last:t AND %s AND path:%s" % 
                                            (repo_name, hit['path']))
                            writer.delete_by_query(q)

                        # index from the previous last changeset + all new ones
                        self.index_changesets(writer, repo_name, repo, last_rev)
                        writer_is_dirty = True

            finally:
                if writer_is_dirty:
                    log.debug('>> COMMITING CHANGES TO CHANGESET INDEX<<')
                    writer.commit(merge=True)
                    log.debug('>> COMMITTED CHANGES TO CHANGESET INDEX<<')
                else:
                    writer.cancel

    def update_file_index(self):
        log.debug((u'STARTING INCREMENTAL INDEXING UPDATE FOR EXTENSIONS %s '
                   'AND REPOS %s') % (INDEX_EXTENSIONS, self.repo_paths.keys()))

        idx = open_dir(self.index_location, indexname=self.indexname)
        # The set of all paths in the index
        indexed_paths = set()
        # The set of all paths we need to re-index
        to_index = set()

        writer = idx.writer()
        writer_is_dirty = False
        try:
            with idx.reader() as reader:

                # Loop over the stored fields in the index
                for fields in reader.all_stored_fields():
                    indexed_path = fields['path']
                    indexed_repo_path = fields['repository']
                    indexed_paths.add(indexed_path)

                    if not indexed_repo_path in self.filtered_repo_update_paths:
                        continue

                    repo = self.repo_paths[indexed_repo_path]

                    try:
                        node = self.get_node(repo, indexed_path)
                        # Check if this file was changed since it was indexed
                        indexed_time = fields['modtime']
                        mtime = self.get_node_mtime(node)
                        if mtime > indexed_time:
                            # The file has changed, delete it and add it to the list of
                            # files to reindex
                            log.debug('adding to reindex list %s mtime: %s vs %s' % (
                                            indexed_path, mtime, indexed_time)
                            )
                            writer.delete_by_term('fileid', indexed_path)
                            writer_is_dirty = True

                            to_index.add(indexed_path)
                    except (ChangesetError, NodeDoesNotExistError):
                        # This file was deleted since it was indexed
                        log.debug('removing from index %s' % indexed_path)
                        writer.delete_by_term('path', indexed_path)
                        writer_is_dirty = True

            # Loop over the files in the filesystem
            # Assume we have a function that gathers the filenames of the
            # documents to be indexed
            ri_cnt_total = 0  # indexed
            riwc_cnt_total = 0  # indexed with content
            for repo_name, repo in self.repo_paths.items():
                # skip indexing if there aren't any revisions
                if len(repo) < 1:
                    continue
                ri_cnt = 0   # indexed
                riwc_cnt = 0  # indexed with content
                for path in self.get_paths(repo):
                    path = safe_unicode(path)
                    if path in to_index or path not in indexed_paths:

                        # This is either a file that's changed, or a new file
                        # that wasn't indexed before. So index it!
                        i, iwc = self.add_doc(writer, path, repo, repo_name)
                        writer_is_dirty = True
                        log.debug('re indexing %s' % path)
                        ri_cnt += i
                        ri_cnt_total += 1
                        riwc_cnt += iwc
                        riwc_cnt_total += iwc
                log.debug('added %s files %s with content for repo %s' % (
                             ri_cnt + riwc_cnt, riwc_cnt, repo.path)
                )
            log.debug('indexed %s files in total and %s with content' % (
                        ri_cnt_total, riwc_cnt_total)
            )
        finally:
            if writer_is_dirty:
                log.debug('>> COMMITING CHANGES <<')
                writer.commit(merge=True)
                log.debug('>>> FINISHED REBUILDING INDEX <<<')
            else:
                writer.cancel()

    def build_indexes(self):
        if os.path.exists(self.index_location):
            log.debug('removing previous index')
            rmtree(self.index_location)

        if not os.path.exists(self.index_location):
            os.mkdir(self.index_location)

        chgset_idx = create_in(self.index_location, CHGSETS_SCHEMA, indexname=CHGSET_IDX_NAME)
        chgset_idx_writer = chgset_idx.writer()

        file_idx = create_in(self.index_location, SCHEMA, indexname=IDX_NAME)
        file_idx_writer = file_idx.writer()
        log.debug('BUILDING INDEX FOR EXTENSIONS %s '
                  'AND REPOS %s' % (INDEX_EXTENSIONS, self.repo_paths.keys()))

        for repo_name, repo in self.repo_paths.items():
            # skip indexing if there aren't any revisions
            if len(repo) < 1:
                continue

            self.index_files(file_idx_writer, repo_name, repo)
            self.index_changesets(chgset_idx_writer, repo_name, repo)

        log.debug('>> COMMITING CHANGES <<')
        file_idx_writer.commit(merge=True)
        chgset_idx_writer.commit(merge=True)
        log.debug('>>> FINISHED BUILDING INDEX <<<')

    def update_indexes(self):
        self.update_file_index()
        self.update_changeset_index()

    def run(self, full_index=False):
        """Run daemon"""
        if full_index or self.initial:
            self.build_indexes()
        else:
            self.update_indexes()
