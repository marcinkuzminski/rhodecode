   
def get_repo_slug(request):
    path_info = request.environ.get('PATH_INFO')
    repo_name = path_info.split('/')[-2]
    action = path_info.split('/')[-1]
    
    return repo_name
