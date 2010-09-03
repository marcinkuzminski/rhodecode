#!/usr/bin/env python
# encoding: utf-8
# whoosh indexer daemon for hg-app
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
Created on Jan 26, 2010

@author: marcink
A deamon will read from task table and run tasks
"""
import sys
import os
from os.path import dirname as dn
from os.path import join as jn

#to get the pylons_app import
project_path = dn(dn(dn(dn(os.path.realpath(__file__)))))
sys.path.append(project_path)

from pidlock import LockHeld, DaemonLock
import traceback
from pylons_app.config.environment import load_environment
from pylons_app.model.hg_model import HgModel
from pylons_app.lib.helpers import safe_unicode
from whoosh.index import create_in, open_dir
from shutil import rmtree
from pylons_app.lib.indexers import ANALYZER, INDEX_EXTENSIONS, IDX_LOCATION, \
SCHEMA, IDX_NAME

import logging
import logging.config
logging.config.fileConfig(jn(project_path, 'development.ini'))
log = logging.getLogger('whooshIndexer')

def scan_paths(root_location):
    return HgModel.repo_scan('/', root_location, None, True)

class WhooshIndexingDaemon(object):
    """Deamon for atomic jobs"""

    def __init__(self, indexname='HG_INDEX', repo_location=None):
        self.indexname = indexname
        self.repo_location = repo_location
    
    def get_paths(self, root_dir):
        """recursive walk in root dir and return a set of all path in that dir
        excluding files in .hg dir"""
        index_paths_ = set()
        for path, dirs, files in os.walk(root_dir):
            if path.find('.hg') == -1:
                for f in files:
                    index_paths_.add(jn(path, f))
    
        return index_paths_
    
    def add_doc(self, writer, path, repo):
        """Adding doc to writer"""
        
        ext = unicode(path.split('/')[-1].split('.')[-1].lower())
        #we just index the content of choosen files
        if ext in INDEX_EXTENSIONS:
            log.debug('    >> %s [WITH CONTENT]' % path)
            fobj = open(path, 'rb')
            content = fobj.read()
            fobj.close()
            u_content = safe_unicode(content)
        else:
            log.debug('    >> %s' % path)
            #just index file name without it's content
            u_content = u''
        
        
        
        try:
            os.stat(path)
            writer.add_document(owner=unicode(repo.contact),
                            repository=u"%s" % repo.name,
                            path=u"%s" % path,
                            content=u_content,
                            modtime=os.path.getmtime(path),
                            extension=ext)             
        except OSError, e:
            import errno
            if e.errno == errno.ENOENT:
                log.debug('path %s does not exist or is a broken symlink' % path)
            else:
                raise e                 

    
    def build_index(self):
        if os.path.exists(IDX_LOCATION):
            log.debug('removing previos index')
            rmtree(IDX_LOCATION)
            
        if not os.path.exists(IDX_LOCATION):
            os.mkdir(IDX_LOCATION)
        
        idx = create_in(IDX_LOCATION, SCHEMA, indexname=IDX_NAME)
        writer = idx.writer()
        
        for cnt, repo in enumerate(scan_paths(self.repo_location).values()):
            log.debug('building index @ %s' % repo.path)
        
            for idx_path in self.get_paths(repo.path):
                self.add_doc(writer, idx_path, repo)
        writer.commit(merge=True)
                
        log.debug('>>> FINISHED BUILDING INDEX <<<')
            
    
    def update_index(self):
        log.debug('STARTING INCREMENTAL INDEXING UPDATE')
            
        idx = open_dir(IDX_LOCATION, indexname=self.indexname)
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
    
            if not os.path.exists(indexed_path):
                # This file was deleted since it was indexed
                log.debug('removing from index %s' % indexed_path)
                writer.delete_by_term('path', indexed_path)
    
            else:
                # Check if this file was changed since it
                # was indexed
                indexed_time = fields['modtime']
                
                mtime = os.path.getmtime(indexed_path)
    
                if mtime > indexed_time:
    
                    # The file has changed, delete it and add it to the list of
                    # files to reindex
                    log.debug('adding to reindex list %s' % indexed_path)
                    writer.delete_by_term('path', indexed_path)
                    to_index.add(indexed_path)
                    #writer.commit()
    
        # Loop over the files in the filesystem
        # Assume we have a function that gathers the filenames of the
        # documents to be indexed
        for repo in scan_paths(self.repo_location).values():
            for path in self.get_paths(repo.path):
                if path in to_index or path not in indexed_paths:
                    # This is either a file that's changed, or a new file
                    # that wasn't indexed before. So index it!
                    self.add_doc(writer, path, repo)
                    log.debug('reindexing %s' % path)
    
        writer.commit(merge=True)
        #idx.optimize()
        log.debug('>>> FINISHED <<<')
        
    def run(self, full_index=False):
        """Run daemon"""
        if full_index:
            self.build_index()
        else:
            self.update_index()
        
if __name__ == "__main__":
    arg = sys.argv[1:]
    if not arg:
        sys.stdout.write('Please specify indexing type [full|incremental]' 
                         ' as script arg \n')
        sys.exit()
    if arg[0] == 'full':
        full_index = True
    elif arg[0] == 'incremental':
        # False means looking just for changes
        full_index = False
    else:
        sys.stdout.write('Please use [full|incremental]' 
                         ' as script arg \n')
        sys.exit()
    
    
    repo_location = '/home/hg_repos/*'
    
    try:
        l = DaemonLock()
        WhooshIndexingDaemon(repo_location=repo_location)\
            .run(full_index=full_index)
        l.release()
    except LockHeld:
        sys.exit(1)

