"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from __future__ import with_statement
from routes import Mapper
from pylons_app.lib.utils import check_repo_fast as cr

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
    
    def check_repo(environ, match_dict):
        """
        check for valid repository for proper 404 handling
        @param environ:
        @param match_dict:
        """
        repo_name = match_dict.get('repo_name')
        return not cr(repo_name, config['base_path'])
 
    #REST REPO MAP
    with map.submapper(path_prefix='/_admin', controller='admin/repos') as m:
        m.connect("repos", "/repos",
             action="create", conditions=dict(method=["POST"]))
        m.connect("repos", "/repos",
             action="index", conditions=dict(method=["GET"]))
        m.connect("formatted_repos", "/repos.{format}",
             action="index",
            conditions=dict(method=["GET"]))
        m.connect("new_repo", "/repos/new",
             action="new", conditions=dict(method=["GET"]))
        m.connect("formatted_new_repo", "/repos/new.{format}",
             action="new", conditions=dict(method=["GET"]))
        m.connect("/repos/{repo_name:.*}",
             action="update", conditions=dict(method=["PUT"],
                                              function=check_repo))
        m.connect("/repos/{repo_name:.*}",
             action="delete", conditions=dict(method=["DELETE"],
                                              function=check_repo))
        m.connect("edit_repo", "/repos/{repo_name:.*}/edit",
             action="edit", conditions=dict(method=["GET"],
                                            function=check_repo))
        m.connect("formatted_edit_repo", "/repos/{repo_name:.*}.{format}/edit",
             action="edit", conditions=dict(method=["GET"],
                                            function=check_repo))
        m.connect("repo", "/repos/{repo_name:.*}",
             action="show", conditions=dict(method=["GET"],
                                            function=check_repo))
        m.connect("formatted_repo", "/repos/{repo_name:.*}.{format}",
             action="show", conditions=dict(method=["GET"],
                                            function=check_repo))
        #ajax delete repo perm user
        m.connect('delete_repo_user', "/repos_delete_user/{repo_name:.*}",
             action="delete_perm_user", conditions=dict(method=["DELETE"],
                                                        function=check_repo))
        
    map.resource('user', 'users', controller='admin/users', path_prefix='/_admin')
    map.resource('permission', 'permissions', controller='admin/permissions', path_prefix='/_admin')
    
    #map.resource('setting', 'settings', controller='admin/settings', path_prefix='/_admin', name_prefix='admin_')
    #REST SETTINGS MAP
    with map.submapper(path_prefix='/_admin', controller='admin/settings') as m:
        m.connect("admin_settings", "/settings",
             action="create", conditions=dict(method=["POST"]))
        m.connect("admin_settings", "/settings",
             action="index", conditions=dict(method=["GET"]))
        m.connect("admin_formatted_settings", "/settings.{format}",
             action="index", conditions=dict(method=["GET"]))
        m.connect("admin_new_setting", "/settings/new",
             action="new", conditions=dict(method=["GET"]))
        m.connect("admin_formatted_new_setting", "/settings/new.{format}",
             action="new", conditions=dict(method=["GET"]))
        m.connect("/settings/{setting_id}",
             action="update", conditions=dict(method=["PUT"]))
        m.connect("/settings/{setting_id}",
             action="delete", conditions=dict(method=["DELETE"]))
        m.connect("admin_edit_setting", "/settings/{setting_id}/edit",
             action="edit", conditions=dict(method=["GET"]))
        m.connect("admin_formatted_edit_setting", "/settings/{setting_id}.{format}/edit",
             action="edit", conditions=dict(method=["GET"]))
        m.connect("admin_setting", "/settings/{setting_id}",
             action="show", conditions=dict(method=["GET"]))
        m.connect("admin_formatted_setting", "/settings/{setting_id}.{format}",
             action="show", conditions=dict(method=["GET"]))
        m.connect("admin_settings_my_account", "/my_account",
             action="my_account", conditions=dict(method=["GET"]))
        m.connect("admin_settings_my_account_update", "/my_account_update",
             action="my_account_update", conditions=dict(method=["PUT"]))
    
    #ADMIN
    with map.submapper(path_prefix='/_admin', controller='admin/admin') as m:
        m.connect('admin_home', '', action='index')#main page
        m.connect('admin_add_repo', '/add_repo/{new_repo:[a-z0-9\. _-]*}',
                  action='add_repo')
    
    #LOGIN/LOGOUT
    map.connect('login_home', '/_admin/login', controller='login')
    map.connect('logout_home', '/_admin/logout', controller='login', action='logout')
    map.connect('register', '/_admin/register', controller='login', action='register')
        
    #FEEDS
    map.connect('rss_feed_home', '/{repo_name:.*}/feed/rss',
                controller='feed', action='rss',
                conditions=dict(function=check_repo))
    map.connect('atom_feed_home', '/{repo_name:.*}/feed/atom',
                controller='feed', action='atom',
                conditions=dict(function=check_repo))
    
    
    #OTHERS
    map.connect('changeset_home', '/{repo_name:.*}/changeset/{revision}',
                controller='changeset', revision='tip',
                conditions=dict(function=check_repo))
    map.connect('summary_home', '/{repo_name:.*}/summary',
                controller='summary', conditions=dict(function=check_repo))
    map.connect('shortlog_home', '/{repo_name:.*}/shortlog',
                controller='shortlog', conditions=dict(function=check_repo))
    map.connect('branches_home', '/{repo_name:.*}/branches',
                controller='branches', conditions=dict(function=check_repo))
    map.connect('tags_home', '/{repo_name:.*}/tags',
                controller='tags', conditions=dict(function=check_repo))
    map.connect('changelog_home', '/{repo_name:.*}/changelog',
                controller='changelog', conditions=dict(function=check_repo))    
    map.connect('files_home', '/{repo_name:.*}/files/{revision}/{f_path:.*}',
                controller='files', revision='tip', f_path='',
                conditions=dict(function=check_repo))
    map.connect('files_diff_home', '/{repo_name:.*}/diff/{f_path:.*}',
                controller='files', action='diff', revision='tip', f_path='',
                conditions=dict(function=check_repo))
    map.connect('files_raw_home', '/{repo_name:.*}/rawfile/{revision}/{f_path:.*}',
                controller='files', action='rawfile', revision='tip', f_path='',
                conditions=dict(function=check_repo))
    map.connect('files_annotate_home', '/{repo_name:.*}/annotate/{revision}/{f_path:.*}',
                controller='files', action='annotate', revision='tip', f_path='',
                conditions=dict(function=check_repo))    
    map.connect('files_archive_home', '/{repo_name:.*}/archive/{revision}/{fileformat}',
                controller='files', action='archivefile', revision='tip',
                conditions=dict(function=check_repo))
    map.connect('repo_settings_update', '/{repo_name:.*}/settings',
                controller='settings', action="update",
                conditions=dict(method=["PUT"], function=check_repo))
    map.connect('repo_settings_home', '/{repo_name:.*}/settings',
                controller='settings', action='index',
                conditions=dict(function=check_repo))

    
    return map
