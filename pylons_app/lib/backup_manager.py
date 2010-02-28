import logging
from mercurial import config
import tarfile
import os
import datetime
import sys
logging.basicConfig(level = logging.DEBUG,
                    format = "%(asctime)s %(levelname)-5.5s %(message)s")

class BackupManager(object):
    def __init__(self):

        dn = os.path.dirname
        self.backup_file_path = os.path.join(dn(dn(dn(__file__))), 'data')
        cfg = config.config()
        try:
            cfg.read(os.path.join(dn(dn(dn(__file__))), 'hgwebdir.config'))
        except IOError:
            logging.error('Could not read hgwebdir.config')
            sys.exit()
        self.set_repos_path(cfg.items('paths'))
        logging.info('starting backup for %s', self.repos_path)
        logging.info('backup target %s', self.backup_file_path)

        if not os.path.isdir(self.repos_path):
            raise Exception('Not a valid directory in %s' % self.repos_path)

    def set_repos_path(self, paths):
        repos_path = paths[0][1].split('/')
        if repos_path[-1] in ['*', '**']:
            repos_path = repos_path[:-1]
        if repos_path[0] != '/':
            repos_path[0] = '/'
        self.repos_path = os.path.join(*repos_path)

    def backup_repos(self):
        today = datetime.datetime.now().weekday() + 1
        bckp_file = os.path.join(self.backup_file_path,
                                 "mercurial_repos.%s.tar.gz" % today)
        tar = tarfile.open(bckp_file, "w:gz")

        for dir in os.listdir(self.repos_path):
            logging.info('backing up %s', dir)
            tar.add(os.path.join(self.repos_path, dir), dir)
        tar.close()


if __name__ == "__main__":
    bm = BackupManager()
    bm.backup_repos()


