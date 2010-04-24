   
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
