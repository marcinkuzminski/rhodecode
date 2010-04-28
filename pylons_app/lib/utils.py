from mercurial import ui, config
import os
import logging
   
def get_repo_slug(request):
    path_info = request.environ.get('PATH_INFO')
    uri_lst = path_info.split('/')   
    repo_name = uri_lst[1]
    return repo_name

def is_mercurial(environ):
    """
    Returns True if request's target is mercurial server - header
    ``HTTP_ACCEPT`` of such request would start with ``application/mercurial``.
    """
    http_accept = environ.get('HTTP_ACCEPT')
    if http_accept and http_accept.startswith('application/mercurial'):
        return True
    return False

def check_repo_dir(paths):
    repos_path = paths[0][1].split('/')
    if repos_path[-1] in ['*', '**']:
        repos_path = repos_path[:-1]
    if repos_path[0] != '/':
        repos_path[0] = '/'
    if not os.path.isdir(os.path.join(*repos_path)):
        raise Exception('Not a valid repository in %s' % paths[0][1])
        
def make_ui(path='hgwebdir.config', checkpaths=True):        
    """
    A funcion that will read python rc files and make an ui from read options
    
    @param path: path to mercurial config file
    """
    if not os.path.isfile(path):
        logging.error('Unable to read config file %s' % path)
        return False
    #propagated from mercurial documentation
    sections = [
                'alias',
                'auth',
                'decode/encode',
                'defaults',
                'diff',
                'email',
                'extensions',
                'format',
                'merge-patterns',
                'merge-tools',
                'hooks',
                'http_proxy',
                'smtp',
                'patch',
                'paths',
                'profiling',
                'server',
                'trusted',
                'ui',
                'web',
                ]

    baseui = ui.ui()
    cfg = config.config()
    cfg.read(path)
    if checkpaths:check_repo_dir(cfg.items('paths'))

    for section in sections:
        for k, v in cfg.items(section):
            baseui.setconfig(section, k, v)
    
    return baseui



