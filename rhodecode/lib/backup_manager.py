# -*- coding: utf-8 -*-
"""
    rhodecode.lib.backup_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Mercurial repositories backup manager, it allows to backups all
    repositories and send it to backup server using RSA key via ssh.

    :created_on: Feb 28, 2010
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
import tarfile
import datetime
import subprocess

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(levelname)-5.5s %(message)s")


class BackupManager(object):
    def __init__(self, repos_location, rsa_key, backup_server):
        today = datetime.datetime.now().weekday() + 1
        self.backup_file_name = "mercurial_repos.%s.tar.gz" % today

        self.id_rsa_path = self.get_id_rsa(rsa_key)
        self.repos_path = self.get_repos_path(repos_location)
        self.backup_server = backup_server

        self.backup_file_path = '/tmp'

        logging.info('starting backup for %s', self.repos_path)
        logging.info('backup target %s', self.backup_file_path)

    def get_id_rsa(self, rsa_key):
        if not os.path.isfile(rsa_key):
            logging.error('Could not load id_rsa key file in %s', rsa_key)
            sys.exit()
        return rsa_key

    def get_repos_path(self, path):
        if not os.path.isdir(path):
            logging.error('Wrong location for repositories in %s', path)
            sys.exit()
        return path

    def backup_repos(self):
        bckp_file = os.path.join(self.backup_file_path, self.backup_file_name)
        tar = tarfile.open(bckp_file, "w:gz")

        for dir_name in os.listdir(self.repos_path):
            logging.info('backing up %s', dir_name)
            tar.add(os.path.join(self.repos_path, dir_name), dir_name)
        tar.close()
        logging.info('finished backup of mercurial repositories')

    def transfer_files(self):
        params = {
                  'id_rsa_key': self.id_rsa_path,
                  'backup_file': os.path.join(self.backup_file_path,
                                             self.backup_file_name),
                  'backup_server': self.backup_server
                  }
        cmd = ['scp', '-l', '40000', '-i', '%(id_rsa_key)s' % params,
               '%(backup_file)s' % params,
               '%(backup_server)s' % params]

        subprocess.call(cmd)
        logging.info('Transfered file %s to %s', self.backup_file_name, cmd[4])

    def rm_file(self):
        logging.info('Removing file %s', self.backup_file_name)
        os.remove(os.path.join(self.backup_file_path, self.backup_file_name))

if __name__ == "__main__":

    repo_location = '/home/repo_path'
    backup_server = 'root@192.168.1.100:/backups/mercurial'
    rsa_key = '/home/id_rsa'

    B_MANAGER = BackupManager(repo_location, rsa_key, backup_server)
    B_MANAGER.backup_repos()
    B_MANAGER.transfer_files()
    B_MANAGER.rm_file()
