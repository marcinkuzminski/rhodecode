import logging
from mercurial import config
import tarfile
import os
import datetime
import sys
import subprocess
logging.basicConfig(level = logging.DEBUG,
                    format = "%(asctime)s %(levelname)-5.5s %(message)s")

class BackupManager(object):
    def __init__(self):
        self.id_rsa_path = '/home/pylons/id_rsa'
        self.check_id_rsa()
        cur_dir = os.path.realpath(__file__)
        dn = os.path.dirname
        self.backup_file_path = os.path.join(dn(dn(dn(cur_dir))), 'data')
        cfg = config.config()
        try:
            cfg.read(os.path.join(dn(dn(dn(cur_dir))), 'hgwebdir.config'))
        except IOError:
            logging.error('Could not read hgwebdir.config')
            sys.exit()
        self.set_repos_path(cfg.items('paths'))
        logging.info('starting backup for %s', self.repos_path)
        logging.info('backup target %s', self.backup_file_path)

        if not os.path.isdir(self.repos_path):
            raise Exception('Not a valid directory in %s' % self.repos_path)

    def check_id_rsa(self):
        if not os.path.isfile(self.id_rsa_path):
            logging.error('Could not load id_rsa key file in %s', self.id_rsa_path)
            sys.exit()

    def set_repos_path(self, paths):
        repos_path = paths[0][1].split('/')
        if repos_path[-1] in ['*', '**']:
            repos_path = repos_path[:-1]
        if repos_path[0] != '/':
            repos_path[0] = '/'
        self.repos_path = os.path.join(*repos_path)

    def backup_repos(self):
        today = datetime.datetime.now().weekday() + 1
        self.backup_file_name = "mercurial_repos.%s.tar.gz" % today
        bckp_file = os.path.join(self.backup_file_path, self.backup_file_name)
        tar = tarfile.open(bckp_file, "w:gz")

        for dir in os.listdir(self.repos_path):
            logging.info('backing up %s', dir)
            tar.add(os.path.join(self.repos_path, dir), dir)
        tar.close()
        logging.info('finished backup of mercurial repositories')



    def transfer_files(self):
        params = {
                  'id_rsa_key': self.id_rsa_path,
                  'backup_file_path':self.backup_file_path,
                  'backup_file_name':self.backup_file_name,
                  }
        cmd = ['scp', '-i', '%(id_rsa_key)s' % params,
               '%(backup_file_path)s/%(backup_file_name)s' % params,
               'root@192.168.2.102:/backups/mercurial' % params]

        subprocess.Popen(cmd)
        logging.info('Transfered file %s to %s', self.backup_file_name, cmd[4])


if __name__ == "__main__":
    bm = BackupManager()
    bm.backup_repos()
    bm.transfer_files()


