   
def get_repo_slug(request):
    path_info = request.environ.get('PATH_INFO')
    uri_lst = path_info.split('/')
    print uri_lst
    print 'len', len(uri_lst)    
    repo_name = uri_lst[1]
    return repo_name
