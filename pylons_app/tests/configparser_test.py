import os
p = os.path.dirname(__file__)
repos = os.path.join(p, '../..', 'hgwebdir.config')
#repos = "/home/marcink/python_workspace/hg_app/hgwebdir.config"
print repos
from ConfigParser import ConfigParser

cp = ConfigParser()

cp.read(repos)
print cp.get('paths', '/')
