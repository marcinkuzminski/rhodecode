"""
Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from __future__ import with_statement
from routes import Mapper


# prefix for non repository related links needs to be prefixed with `/`
ADMIN_PREFIX = '/_admin'


def make_map(config):
    """Create, configure and return the routes Mapper"""
    rmap = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    rmap.minimization = False
    rmap.explicit = False

    from rhodecode.lib.utils import is_valid_repo
    from rhodecode.lib.utils import is_valid_repos_group

    def check_repo(environ, match_dict):
        """
        check for valid repository for proper 404 handling
        
        :param environ:
        :param match_dict:
        """

        repo_name = match_dict.get('repo_name')
        return is_valid_repo(repo_name, config['base_path'])

    def check_group(environ, match_dict):
        """
        check for valid repositories group for proper 404 handling
        
        :param environ:
        :param match_dict:
        """
        repos_group_name = match_dict.get('group_name')

        return is_valid_repos_group(repos_group_name, config['base_path'])


    def check_int(environ, match_dict):
        return match_dict.get('id').isdigit()

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    rmap.connect('/error/{action}', controller='error')
    rmap.connect('/error/{action}/{id}', controller='error')

    #==========================================================================
    # CUSTOM ROUTES HERE
    #==========================================================================

    #MAIN PAGE
    rmap.connect('home', '/', controller='home', action='index')
    rmap.connect('repo_switcher', '/repos', controller='home',
                 action='repo_switcher')
    rmap.connect('bugtracker',
                 "http://bitbucket.org/marcinkuzminski/rhodecode/issues",
                 _static=True)
    rmap.connect('rhodecode_official', "http://rhodecode.org", _static=True)

    #ADMIN REPOSITORY REST ROUTES
    with rmap.submapper(path_prefix=ADMIN_PREFIX,
                        controller='admin/repos') as m:
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
        m.connect('delete_repo_users_group',
                  "/repos_delete_users_group/{repo_name:.*}",
                  action="delete_perm_users_group",
                  conditions=dict(method=["DELETE"], function=check_repo))

        #settings actions
        m.connect('repo_stats', "/repos_stats/{repo_name:.*}",
             action="repo_stats", conditions=dict(method=["DELETE"],
                                                        function=check_repo))
        m.connect('repo_cache', "/repos_cache/{repo_name:.*}",
             action="repo_cache", conditions=dict(method=["DELETE"],
                                                        function=check_repo))
        m.connect('repo_public_journal',
                  "/repos_public_journal/{repo_name:.*}",
                  action="repo_public_journal", conditions=dict(method=["PUT"],
                  function=check_repo))
        m.connect('repo_pull', "/repo_pull/{repo_name:.*}",
             action="repo_pull", conditions=dict(method=["PUT"],
                                                        function=check_repo))

    with rmap.submapper(path_prefix=ADMIN_PREFIX,
                        controller='admin/repos_groups') as m:
        m.connect("repos_groups", "/repos_groups",
                  action="create", conditions=dict(method=["POST"]))
        m.connect("repos_groups", "/repos_groups",
                  action="index", conditions=dict(method=["GET"]))
        m.connect("formatted_repos_groups", "/repos_groups.{format}",
                  action="index", conditions=dict(method=["GET"]))
        m.connect("new_repos_group", "/repos_groups/new",
                  action="new", conditions=dict(method=["GET"]))
        m.connect("formatted_new_repos_group", "/repos_groups/new.{format}",
                  action="new", conditions=dict(method=["GET"]))
        m.connect("update_repos_group", "/repos_groups/{id}",
                  action="update", conditions=dict(method=["PUT"],
                                                   function=check_int))
        m.connect("delete_repos_group", "/repos_groups/{id}",
                  action="delete", conditions=dict(method=["DELETE"],
                                                   function=check_int))
        m.connect("edit_repos_group", "/repos_groups/{id}/edit",
                  action="edit", conditions=dict(method=["GET"],
                                                 function=check_int))
        m.connect("formatted_edit_repos_group",
                  "/repos_groups/{id}.{format}/edit",
                  action="edit", conditions=dict(method=["GET"],
                                                 function=check_int))
        m.connect("repos_group", "/repos_groups/{id}",
                  action="show", conditions=dict(method=["GET"],
                                                 function=check_int))
        m.connect("formatted_repos_group", "/repos_groups/{id}.{format}",
                  action="show", conditions=dict(method=["GET"],
                                                 function=check_int))

    #ADMIN USER REST ROUTES
    with rmap.submapper(path_prefix=ADMIN_PREFIX,
                        controller='admin/users') as m:
        m.connect("users", "/users",
                  action="create", conditions=dict(method=["POST"]))
        m.connect("users", "/users",
                  action="index", conditions=dict(method=["GET"]))
        m.connect("formatted_users", "/users.{format}",
                  action="index", conditions=dict(method=["GET"]))
        m.connect("new_user", "/users/new",
                  action="new", conditions=dict(method=["GET"]))
        m.connect("formatted_new_user", "/users/new.{format}",
                  action="new", conditions=dict(method=["GET"]))
        m.connect("update_user", "/users/{id}",
                  action="update", conditions=dict(method=["PUT"]))
        m.connect("delete_user", "/users/{id}",
                  action="delete", conditions=dict(method=["DELETE"]))
        m.connect("edit_user", "/users/{id}/edit",
                  action="edit", conditions=dict(method=["GET"]))
        m.connect("formatted_edit_user",
                  "/users/{id}.{format}/edit",
                  action="edit", conditions=dict(method=["GET"]))
        m.connect("user", "/users/{id}",
                  action="show", conditions=dict(method=["GET"]))
        m.connect("formatted_user", "/users/{id}.{format}",
                  action="show", conditions=dict(method=["GET"]))

        #EXTRAS USER ROUTES
        m.connect("user_perm", "/users_perm/{id}",
                  action="update_perm", conditions=dict(method=["PUT"]))

    #ADMIN USERS REST ROUTES
    with rmap.submapper(path_prefix=ADMIN_PREFIX,
                        controller='admin/users_groups') as m:
        m.connect("users_groups", "/users_groups",
                  action="create", conditions=dict(method=["POST"]))
        m.connect("users_groups", "/users_groups",
                  action="index", conditions=dict(method=["GET"]))
        m.connect("formatted_users_groups", "/users_groups.{format}",
                  action="index", conditions=dict(method=["GET"]))
        m.connect("new_users_group", "/users_groups/new",
                  action="new", conditions=dict(method=["GET"]))
        m.connect("formatted_new_users_group", "/users_groups/new.{format}",
                  action="new", conditions=dict(method=["GET"]))
        m.connect("update_users_group", "/users_groups/{id}",
                  action="update", conditions=dict(method=["PUT"]))
        m.connect("delete_users_group", "/users_groups/{id}",
                  action="delete", conditions=dict(method=["DELETE"]))
        m.connect("edit_users_group", "/users_groups/{id}/edit",
                  action="edit", conditions=dict(method=["GET"]))
        m.connect("formatted_edit_users_group",
                  "/users_groups/{id}.{format}/edit",
                  action="edit", conditions=dict(method=["GET"]))
        m.connect("users_group", "/users_groups/{id}",
                  action="show", conditions=dict(method=["GET"]))
        m.connect("formatted_users_group", "/users_groups/{id}.{format}",
                  action="show", conditions=dict(method=["GET"]))

        #EXTRAS USER ROUTES
        m.connect("users_group_perm", "/users_groups_perm/{id}",
                  action="update_perm", conditions=dict(method=["PUT"]))

    #ADMIN GROUP REST ROUTES
    rmap.resource('group', 'groups',
                  controller='admin/groups', path_prefix=ADMIN_PREFIX)

    #ADMIN PERMISSIONS REST ROUTES
    rmap.resource('permission', 'permissions',
                  controller='admin/permissions', path_prefix=ADMIN_PREFIX)

    ##ADMIN LDAP SETTINGS
    rmap.connect('ldap_settings', '%s/ldap' % ADMIN_PREFIX,
                 controller='admin/ldap_settings', action='ldap_settings',
                 conditions=dict(method=["POST"]))

    rmap.connect('ldap_home', '%s/ldap' % ADMIN_PREFIX,
                 controller='admin/ldap_settings')

    #ADMIN SETTINGS REST ROUTES
    with rmap.submapper(path_prefix=ADMIN_PREFIX,
                        controller='admin/settings') as m:
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
        m.connect("formatted_admin_edit_setting",
                  "/settings/{setting_id}.{format}/edit",
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
    with rmap.submapper(path_prefix=ADMIN_PREFIX,
                        controller='admin/admin') as m:
        m.connect('admin_home', '', action='index')
        m.connect('admin_add_repo', '/add_repo/{new_repo:[a-z0-9\. _-]*}',
                  action='add_repo')

    #==========================================================================
    # API V1
    #==========================================================================
    with rmap.submapper(path_prefix=ADMIN_PREFIX,
                        controller='api/api') as m:
        m.connect('api', '/api')


    #USER JOURNAL
    rmap.connect('journal', '%s/journal' % ADMIN_PREFIX, controller='journal')

    rmap.connect('public_journal', '%s/public_journal' % ADMIN_PREFIX,
                 controller='journal', action="public_journal")

    rmap.connect('public_journal_rss', '%s/public_journal_rss' % ADMIN_PREFIX,
                 controller='journal', action="public_journal_rss")

    rmap.connect('public_journal_atom',
                 '%s/public_journal_atom' % ADMIN_PREFIX, controller='journal',
                 action="public_journal_atom")

    rmap.connect('toggle_following', '%s/toggle_following' % ADMIN_PREFIX,
                 controller='journal', action='toggle_following',
                 conditions=dict(method=["POST"]))

    #SEARCH
    rmap.connect('search', '%s/search' % ADMIN_PREFIX, controller='search',)
    rmap.connect('search_repo', '%s/search/{search_repo:.*}' % ADMIN_PREFIX,
                  controller='search')

    #LOGIN/LOGOUT/REGISTER/SIGN IN
    rmap.connect('login_home', '%s/login' % ADMIN_PREFIX, controller='login')
    rmap.connect('logout_home', '%s/logout' % ADMIN_PREFIX, controller='login',
                 action='logout')

    rmap.connect('register', '%s/register' % ADMIN_PREFIX, controller='login',
                 action='register')

    rmap.connect('reset_password', '%s/password_reset' % ADMIN_PREFIX,
                 controller='login', action='password_reset')

    rmap.connect('reset_password_confirmation',
                 '%s/password_reset_confirmation' % ADMIN_PREFIX,
                 controller='login', action='password_reset_confirmation')

    #FEEDS
    rmap.connect('rss_feed_home', '/{repo_name:.*}/feed/rss',
                controller='feed', action='rss',
                conditions=dict(function=check_repo))

    rmap.connect('atom_feed_home', '/{repo_name:.*}/feed/atom',
                controller='feed', action='atom',
                conditions=dict(function=check_repo))

    #==========================================================================
    # REPOSITORY ROUTES
    #==========================================================================
    rmap.connect('summary_home', '/{repo_name:.*}',
                controller='summary',
                conditions=dict(function=check_repo))

    rmap.connect('repos_group_home', '/{group_name:.*}',
                controller='admin/repos_groups', action="show_by_name",
                conditions=dict(function=check_group))

    rmap.connect('changeset_home', '/{repo_name:.*}/changeset/{revision}',
                controller='changeset', revision='tip',
                conditions=dict(function=check_repo))

    rmap.connect('raw_changeset_home',
                 '/{repo_name:.*}/raw-changeset/{revision}',
                 controller='changeset', action='raw_changeset',
                 revision='tip', conditions=dict(function=check_repo))

    rmap.connect('summary_home', '/{repo_name:.*}/summary',
                controller='summary', conditions=dict(function=check_repo))

    rmap.connect('shortlog_home', '/{repo_name:.*}/shortlog',
                controller='shortlog', conditions=dict(function=check_repo))

    rmap.connect('branches_home', '/{repo_name:.*}/branches',
                controller='branches', conditions=dict(function=check_repo))

    rmap.connect('tags_home', '/{repo_name:.*}/tags',
                controller='tags', conditions=dict(function=check_repo))

    rmap.connect('changelog_home', '/{repo_name:.*}/changelog',
                controller='changelog', conditions=dict(function=check_repo))

    rmap.connect('changelog_details', '/{repo_name:.*}/changelog_details/{cs}',
                controller='changelog', action='changelog_details',
                conditions=dict(function=check_repo))

    rmap.connect('files_home', '/{repo_name:.*}/files/{revision}/{f_path:.*}',
                controller='files', revision='tip', f_path='',
                conditions=dict(function=check_repo))

    rmap.connect('files_diff_home', '/{repo_name:.*}/diff/{f_path:.*}',
                controller='files', action='diff', revision='tip', f_path='',
                conditions=dict(function=check_repo))

    rmap.connect('files_rawfile_home',
                 '/{repo_name:.*}/rawfile/{revision}/{f_path:.*}',
                 controller='files', action='rawfile', revision='tip',
                 f_path='', conditions=dict(function=check_repo))

    rmap.connect('files_raw_home',
                 '/{repo_name:.*}/raw/{revision}/{f_path:.*}',
                 controller='files', action='raw', revision='tip', f_path='',
                 conditions=dict(function=check_repo))

    rmap.connect('files_annotate_home',
                 '/{repo_name:.*}/annotate/{revision}/{f_path:.*}',
                 controller='files', action='annotate', revision='tip',
                 f_path='', conditions=dict(function=check_repo))

    rmap.connect('files_edit_home',
                 '/{repo_name:.*}/edit/{revision}/{f_path:.*}',
                 controller='files', action='edit', revision='tip',
                 f_path='', conditions=dict(function=check_repo))

    rmap.connect('files_add_home',
                 '/{repo_name:.*}/add/{revision}/{f_path:.*}',
                 controller='files', action='add', revision='tip',
                 f_path='', conditions=dict(function=check_repo))

    rmap.connect('files_archive_home', '/{repo_name:.*}/archive/{fname}',
                controller='files', action='archivefile',
                conditions=dict(function=check_repo))

    rmap.connect('files_nodelist_home',
                 '/{repo_name:.*}/nodelist/{revision}/{f_path:.*}',
                controller='files', action='nodelist',
                conditions=dict(function=check_repo))

    rmap.connect('repo_settings_delete', '/{repo_name:.*}/settings',
                controller='settings', action="delete",
                conditions=dict(method=["DELETE"], function=check_repo))

    rmap.connect('repo_settings_update', '/{repo_name:.*}/settings',
                controller='settings', action="update",
                conditions=dict(method=["PUT"], function=check_repo))

    rmap.connect('repo_settings_home', '/{repo_name:.*}/settings',
                controller='settings', action='index',
                conditions=dict(function=check_repo))

    rmap.connect('repo_fork_create_home', '/{repo_name:.*}/fork',
                controller='settings', action='fork_create',
                conditions=dict(function=check_repo, method=["POST"]))

    rmap.connect('repo_fork_home', '/{repo_name:.*}/fork',
                controller='settings', action='fork',
                conditions=dict(function=check_repo))

    rmap.connect('repo_followers_home', '/{repo_name:.*}/followers',
                 controller='followers', action='followers',
                 conditions=dict(function=check_repo))

    rmap.connect('repo_forks_home', '/{repo_name:.*}/forks',
                 controller='forks', action='forks',
                 conditions=dict(function=check_repo))

    return rmap
