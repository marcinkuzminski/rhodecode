"""
Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from __future__ import with_statement
from routes import Mapper
from rhodecode.lib.utils import check_repo_fast as cr

def make_map(config):
    """Create, configure and return the routes Mapper"""
    routes_map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    routes_map.minimization = False
    routes_map.explicit = False

    def check_repo(environ, match_dict):
        """
        check for valid repository for proper 404 handling
        
        :param environ:
        :param match_dict:
        """
        repo_name = match_dict.get('repo_name')
        return not cr(repo_name, config['base_path'])

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    routes_map.connect('/error/{action}', controller='error')
    routes_map.connect('/error/{action}/{id}', controller='error')

    #==========================================================================
    # CUSTOM ROUTES HERE
    #==========================================================================

    #MAIN PAGE
    routes_map.connect('home', '/', controller='home', action='index')
    routes_map.connect('bugtracker', "http://bitbucket.org/marcinkuzminski/rhodecode/issues", _static=True)
    routes_map.connect('gpl_license', "http://www.gnu.org/licenses/gpl.html", _static=True)
    #ADMIN REPOSITORY REST ROUTES
    with routes_map.submapper(path_prefix='/_admin', controller='admin/repos') as m:
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
        #ajax delete repo perm users_group
        m.connect('delete_repo_users_group', "/repos_delete_users_group/{repo_name:.*}",
             action="delete_perm_users_group", conditions=dict(method=["DELETE"],
                                                        function=check_repo))

        #settings actions
        m.connect('repo_stats', "/repos_stats/{repo_name:.*}",
             action="repo_stats", conditions=dict(method=["DELETE"],
                                                        function=check_repo))
        m.connect('repo_cache', "/repos_cache/{repo_name:.*}",
             action="repo_cache", conditions=dict(method=["DELETE"],
                                                        function=check_repo))
        m.connect('repo_public_journal', "/repos_public_journal/{repo_name:.*}",
             action="repo_public_journal", conditions=dict(method=["PUT"],
                                                        function=check_repo))

    #ADMIN USER REST ROUTES
    routes_map.resource('user', 'users', controller='admin/users', path_prefix='/_admin')

    #ADMIN USER REST ROUTES
    routes_map.resource('users_group', 'users_groups', controller='admin/users_groups', path_prefix='/_admin')

    #ADMIN GROUP REST ROUTES
    routes_map.resource('group', 'groups', controller='admin/groups', path_prefix='/_admin')

    #ADMIN PERMISSIONS REST ROUTES
    routes_map.resource('permission', 'permissions', controller='admin/permissions', path_prefix='/_admin')

    ##ADMIN LDAP SETTINGS
    routes_map.connect('ldap_settings', '/_admin/ldap', controller='admin/ldap_settings',
                action='ldap_settings', conditions=dict(method=["POST"]))
    routes_map.connect('ldap_home', '/_admin/ldap', controller='admin/ldap_settings',)


    #ADMIN SETTINGS REST ROUTES
    with routes_map.submapper(path_prefix='/_admin', controller='admin/settings') as m:
        m.connect("admin_settings", "/settings",
             action="create", conditions=dict(method=["POST"]))
        m.connect("admin_settings", "/settings",
             action="index", conditions=dict(method=["GET"]))
        m.connect("formatted_admin_settings", "/settings.{format}",
             action="index", conditions=dict(method=["GET"]))
        m.connect("admin_new_setting", "/settings/new",
             action="new", conditions=dict(method=["GET"]))
        m.connect("formatted_admin_new_setting", "/settings/new.{format}",
             action="new", conditions=dict(method=["GET"]))
        m.connect("/settings/{setting_id}",
             action="update", conditions=dict(method=["PUT"]))
        m.connect("/settings/{setting_id}",
             action="delete", conditions=dict(method=["DELETE"]))
        m.connect("admin_edit_setting", "/settings/{setting_id}/edit",
             action="edit", conditions=dict(method=["GET"]))
        m.connect("formatted_admin_edit_setting", "/settings/{setting_id}.{format}/edit",
             action="edit", conditions=dict(method=["GET"]))
        m.connect("admin_setting", "/settings/{setting_id}",
             action="show", conditions=dict(method=["GET"]))
        m.connect("formatted_admin_setting", "/settings/{setting_id}.{format}",
             action="show", conditions=dict(method=["GET"]))
        m.connect("admin_settings_my_account", "/my_account",
             action="my_account", conditions=dict(method=["GET"]))
        m.connect("admin_settings_my_account_update", "/my_account_update",
             action="my_account_update", conditions=dict(method=["PUT"]))
        m.connect("admin_settings_create_repository", "/create_repository",
             action="create_repository", conditions=dict(method=["GET"]))

    #ADMIN MAIN PAGES
    with routes_map.submapper(path_prefix='/_admin', controller='admin/admin') as m:
        m.connect('admin_home', '', action='index')#main page
        m.connect('admin_add_repo', '/add_repo/{new_repo:[a-z0-9\. _-]*}',
                  action='add_repo')


    #USER JOURNAL
    routes_map.connect('journal', '/_admin/journal', controller='journal',)
    routes_map.connect('public_journal', '/_admin/public_journal', controller='journal',
                       action="public_journal")
    routes_map.connect('toggle_following', '/_admin/toggle_following', controller='journal',
                action='toggle_following', conditions=dict(method=["POST"]))


    #SEARCH
    routes_map.connect('search', '/_admin/search', controller='search',)
    routes_map.connect('search_repo', '/_admin/search/{search_repo:.*}', controller='search')

    #LOGIN/LOGOUT/REGISTER/SIGN IN
    routes_map.connect('login_home', '/_admin/login', controller='login')
    routes_map.connect('logout_home', '/_admin/logout', controller='login', action='logout')
    routes_map.connect('register', '/_admin/register', controller='login', action='register')
    routes_map.connect('reset_password', '/_admin/password_reset', controller='login', action='password_reset')

    #FEEDS
    routes_map.connect('rss_feed_home', '/{repo_name:.*}/feed/rss',
                controller='feed', action='rss',
                conditions=dict(function=check_repo))
    routes_map.connect('atom_feed_home', '/{repo_name:.*}/feed/atom',
                controller='feed', action='atom',
                conditions=dict(function=check_repo))


    #REPOSITORY ROUTES
    routes_map.connect('changeset_home', '/{repo_name:.*}/changeset/{revision}',
                controller='changeset', revision='tip',
                conditions=dict(function=check_repo))
    routes_map.connect('raw_changeset_home', '/{repo_name:.*}/raw-changeset/{revision}',
                controller='changeset', action='raw_changeset', revision='tip',
                conditions=dict(function=check_repo))
    routes_map.connect('summary_home', '/{repo_name:.*}',
                controller='summary', conditions=dict(function=check_repo))
    routes_map.connect('summary_home', '/{repo_name:.*}/summary',
                controller='summary', conditions=dict(function=check_repo))
    routes_map.connect('shortlog_home', '/{repo_name:.*}/shortlog',
                controller='shortlog', conditions=dict(function=check_repo))
    routes_map.connect('branches_home', '/{repo_name:.*}/branches',
                controller='branches', conditions=dict(function=check_repo))
    routes_map.connect('tags_home', '/{repo_name:.*}/tags',
                controller='tags', conditions=dict(function=check_repo))
    routes_map.connect('changelog_home', '/{repo_name:.*}/changelog',
                controller='changelog', conditions=dict(function=check_repo))
    routes_map.connect('files_home', '/{repo_name:.*}/files/{revision}/{f_path:.*}',
                controller='files', revision='tip', f_path='',
                conditions=dict(function=check_repo))
    routes_map.connect('files_diff_home', '/{repo_name:.*}/diff/{f_path:.*}',
                controller='files', action='diff', revision='tip', f_path='',
                conditions=dict(function=check_repo))
    routes_map.connect('files_rawfile_home', '/{repo_name:.*}/rawfile/{revision}/{f_path:.*}',
                controller='files', action='rawfile', revision='tip', f_path='',
                conditions=dict(function=check_repo))
    routes_map.connect('files_raw_home', '/{repo_name:.*}/raw/{revision}/{f_path:.*}',
                controller='files', action='raw', revision='tip', f_path='',
                conditions=dict(function=check_repo))
    routes_map.connect('files_annotate_home', '/{repo_name:.*}/annotate/{revision}/{f_path:.*}',
                controller='files', action='annotate', revision='tip', f_path='',
                conditions=dict(function=check_repo))
    routes_map.connect('files_archive_home', '/{repo_name:.*}/archive/{fname}',
                controller='files', action='archivefile',
                conditions=dict(function=check_repo))
    routes_map.connect('repo_settings_delete', '/{repo_name:.*}/settings',
                controller='settings', action="delete",
                conditions=dict(method=["DELETE"], function=check_repo))
    routes_map.connect('repo_settings_update', '/{repo_name:.*}/settings',
                controller='settings', action="update",
                conditions=dict(method=["PUT"], function=check_repo))
    routes_map.connect('repo_settings_home', '/{repo_name:.*}/settings',
                controller='settings', action='index',
                conditions=dict(function=check_repo))

    routes_map.connect('repo_fork_create_home', '/{repo_name:.*}/fork',
                controller='settings', action='fork_create',
                conditions=dict(function=check_repo, method=["POST"]))
    routes_map.connect('repo_fork_home', '/{repo_name:.*}/fork',
                controller='settings', action='fork',
                conditions=dict(function=check_repo))

    return routes_map
