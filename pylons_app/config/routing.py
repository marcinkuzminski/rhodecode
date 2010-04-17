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
    
    map.resource('repo', 'repos', path_prefix='/_admin')
    map.resource('user', 'users', path_prefix='/_admin')
    
    
    with map.submapper(path_prefix='/_admin', controller='admin') as m:
        m.connect('admin_home', '/', action='index')#main page
        m.connect('admin_add_repo', '/add_repo/{new_repo:[a-z0-9\. _-]*}', action='add_repo')
    
    
    map.connect('summary_home', '/{repo_name}/_summary', controller='summary')
    
    map.connect('hg', '/{path_info:.*}', controller='hg',
                action="view", path_info='/')

    return map
