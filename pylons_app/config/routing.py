"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from routes import Mapper

def make_map(config):
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    map.minimization = False
    map.explicit = False

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    # CUSTOM ROUTES HERE
    map.connect('hg_home', '/', controller='hg', action='index')
    
    
    #REST controllers
    map.resource('repo', 'repos', path_prefix='/_admin')
    map.resource('user', 'users', path_prefix='/_admin')
    
    #ADMIN
    with map.submapper(path_prefix='/_admin', controller='admin') as m:
        m.connect('admin_home', '/', action='index')#main page
        m.connect('admin_add_repo', '/add_repo/{new_repo:[a-z0-9\. _-]*}',
                  action='add_repo')
    
    map.connect('login_home', '/login', controller='login')
    map.connect('logout_home', '/logout', controller='login', action='logout')
    
    map.connect('changeset_home', '/{repo_name}/changeset/{revision}',
                controller='changeset', revision='tip')
    map.connect('summary_home', '/{repo_name}/summary',
                controller='summary')
    map.connect('shortlog_home', '/{repo_name}/shortlog/',
                controller='shortlog')
    map.connect('branches_home', '/{repo_name}/branches',
                controller='branches')
    map.connect('tags_home', '/{repo_name}/tags',
                controller='tags')
    map.connect('changelog_home', '/{repo_name}/changelog',
                controller='changelog')    
    map.connect('files_home', '/{repo_name}/files/{revision}/{f_path:.*}',
                controller='files', revision='tip', f_path='')
    map.connect('files_diff_home', '/{repo_name}/diff/{f_path:.*}',
                controller='files', action='diff', revision='tip', f_path='')
    map.connect('files_raw_home', '/{repo_name}/rawfile/{revision}/{f_path:.*}',
                controller='files', action='rawfile', revision='tip', f_path='')
    map.connect('files_annotate_home', '/{repo_name}/annotate/{revision}/{f_path:.*}',
                controller='files', action='annotate', revision='tip', f_path='')    
    map.connect('files_archive_home', '/{repo_name}/archive/{revision}/{fileformat}',
                controller='files', action='archivefile', revision='tip')
    return map
