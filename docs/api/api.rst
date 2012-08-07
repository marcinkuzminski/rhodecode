.. _api:

===
API
===


Starting from RhodeCode version 1.2 a simple API was implemented.
There's a single schema for calling all api methods. API is implemented
with JSON protocol both ways. An url to send API request to RhodeCode is
<your_server>/_admin/api

API ACCESS FOR WEB VIEWS
++++++++++++++++++++++++

API access can also be turned on for each web view in RhodeCode that is 
decorated with `@LoginRequired` decorator. To enable API access simple change 
the standard login decorator to `@LoginRequired(api_access=True)`. 
After this change, a rhodecode view can be accessed without login by adding a 
GET parameter `?api_key=<api_key>` to url. By default this is only
enabled on RSS/ATOM feed views.


API ACCESS
++++++++++

All clients are required to send JSON-RPC spec JSON data::

    {   
        "id:"<id>",
        "api_key":"<api_key>",
        "method":"<method_name>",
        "args":{"<arg_key>":"<arg_val>"}
    }

Example call for autopulling remotes repos using curl::
    curl https://server.com/_admin/api -X POST -H 'content-type:text/plain' --data-binary '{"id":1,"api_key":"xe7cdb2v278e4evbdf5vs04v832v0efvcbcve4a3","method":"pull","args":{"repo":"CPython"}}'

Simply provide
 - *id* A value of any type, which is used to match the response with the request that it is replying to.
 - *api_key* for access and permission validation.
 - *method* is name of method to call
 - *args* is an key:value list of arguments to pass to method

.. note::

    api_key can be found in your user account page


RhodeCode API will return always a JSON-RPC response::

    {   
        "id":<id>, # matching id sent by request
        "result": "<result>"|null, # JSON formatted result, null if any errors
        "error": "null"|<error_message> # JSON formatted error (if any)
    }

All responses from API will be `HTTP/1.0 200 OK`, if there's an error while
calling api *error* key from response will contain failure description
and result will be null.


API CLIENT
++++++++++

From version 1.4 RhodeCode adds a script that allows to easily
communicate with API. After installing RhodeCode a `rhodecode-api` script
will be available.

To get started quickly simply run::

  rhodecode-api _create_config --apikey=<youapikey> --apihost=<rhodecode host>
 
This will create a file named .config in the directory you executed it storing
json config file with credentials. You can skip this step and always provide
both of the arguments to be able to communicate with server


after that simply run any api command for example get_repo::
 
 rhodecode-api get_repo

 calling {"api_key": "<apikey>", "id": 75, "args": {}, "method": "get_repo"} to http://127.0.0.1:5000
 rhodecode said:
 {'error': 'Missing non optional `repoid` arg in JSON DATA',
  'id': 75,
  'result': None}

Ups looks like we forgot to add an argument

Let's try again now giving the repoid as parameters::

    rhodecode-api get_repo repoid:rhodecode   
 
    calling {"api_key": "<apikey>", "id": 39, "args": {"repoid": "rhodecode"}, "method": "get_repo"} to http://127.0.0.1:5000
    rhodecode said:
    {'error': None,
     'id': 39,
     'result': <json data...>}



API METHODS
+++++++++++


pull
----

Pulls given repo from remote location. Can be used to automatically keep
remote repos up to date. This command can be executed only using api_key
belonging to user with admin rights

INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "pull"
    args :    {
                "repoid" : "<reponame or repo_id>"
              }

OUTPUT::

    id : <id_given_in_input>
    result : "Pulled from `<reponame>`"
    error :  null


rescan_repos
------------

Dispatch rescan repositories action. If remove_obsolete is set
RhodeCode will delete repos that are in database but not in the filesystem.
This command can be executed only using api_key belonging to user with admin 
rights.

INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "rescan_repos"
    args :    {
                "remove_obsolete" : "<boolean = Optional(False)>"
              }

OUTPUT::

    id : <id_given_in_input>
    result : "{'added': [<list of names of added repos>], 
               'removed': [<list of names of removed repos>]}"
    error :  null


get_user
--------

Get's an user by username or user_id, Returns empty result if user is not found.
This command can be executed only using api_key belonging to user with admin 
rights.


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "get_user"
    args :    { 
                "userid" : "<username or user_id>"
              }

OUTPUT::

    id : <id_given_in_input>
    result: None if user does not exist or 
            {
                "user_id" :  "<user_id>",
                "username" : "<username>",
                "firstname": "<firstname>",
                "lastname" : "<lastname>",
                "email" :    "<email>",
                "emails":    "<list_of_all_additional_emails>",
                "active" :   "<bool>",
                "admin" :    "<bool>",
                "ldap_dn" :  "<ldap_dn>",
                "last_login": "<last_login>",
                "permissions": {
                    "global": ["hg.create.repository",
                               "repository.read",
                               "hg.register.manual_activate"],
                    "repositories": {"repo1": "repository.none"},
                    "repositories_groups": {"Group1": "group.read"}
                 },
            }

    error:  null


get_users
---------

Lists all existing users. This command can be executed only using api_key
belonging to user with admin rights.


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "get_users"
    args :    { }

OUTPUT::

    id : <id_given_in_input>
    result: [
              {
                "user_id" :  "<user_id>",
                "username" : "<username>",
                "firstname": "<firstname>",
                "lastname" : "<lastname>",
                "email" :    "<email>",
                "emails":    "<list_of_all_additional_emails>",
                "active" :   "<bool>",
                "admin" :    "<bool>",
                "ldap_dn" :  "<ldap_dn>",
                "last_login": "<last_login>",
              },
    	      …
            ]
    error:  null


create_user
-----------

Creates new user. This command can 
be executed only using api_key belonging to user with admin rights.


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "create_user"
    args :    {
                "username" :  "<username>",
                "email" :     "<useremail>",
                "password" :  "<password>",
                "firstname" : "<firstname> = Optional(None)",
                "lastname" :  "<lastname> = Optional(None)",
                "active" :    "<bool> = Optional(True)",
                "admin" :     "<bool> = Optional(False)",
                "ldap_dn" :   "<ldap_dn> = Optional(None)"
              }

OUTPUT::

    id : <id_given_in_input>
    result: {
              "msg" : "created new user `<username>`",
              "user": {
                "user_id" :  "<user_id>",
                "username" : "<username>",
                "firstname": "<firstname>",
                "lastname" : "<lastname>",
                "email" :    "<email>",
                "emails":    "<list_of_all_additional_emails>",
                "active" :   "<bool>",
                "admin" :    "<bool>",
                "ldap_dn" :  "<ldap_dn>",
                "last_login": "<last_login>",
              },
            }
    error:  null


update_user
-----------

updates given user if such user exists. This command can 
be executed only using api_key belonging to user with admin rights.


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "update_user"
    args :    {
                "userid" : "<user_id or username>",
                "username" :  "<username> = Optional",
                "email" :     "<useremail> = Optional",
                "password" :  "<password> = Optional",
                "firstname" : "<firstname> = Optional",
                "lastname" :  "<lastname> = Optional",
                "active" :    "<bool> = Optional",
                "admin" :     "<bool> = Optional",
                "ldap_dn" :   "<ldap_dn> = Optional"
              }

OUTPUT::

    id : <id_given_in_input>
    result: {
              "msg" : "updated user ID:<userid> <username>",
              "user": {
                "user_id" :  "<user_id>",
                "username" : "<username>",
                "firstname": "<firstname>",
                "lastname" : "<lastname>",
                "email" :    "<email>",
                "emails":    "<list_of_all_additional_emails>",
                "active" :   "<bool>",
                "admin" :    "<bool>",
                "ldap_dn" :  "<ldap_dn>",
                "last_login": "<last_login>",
              },              
            }
    error:  null


delete_user
-----------


deletes givenuser if such user exists. This command can 
be executed only using api_key belonging to user with admin rights.


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "delete_user"
    args :    {
                "userid" : "<user_id or username>",
              }

OUTPUT::

    id : <id_given_in_input>
    result: {
              "msg" : "deleted user ID:<userid> <username>",
              "user": null
            }
    error:  null


get_users_group
---------------

Gets an existing users group. This command can be executed only using api_key
belonging to user with admin rights.


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "get_users_group"
    args :    {
                "usersgroupid" : "<users group id or name>"
              }

OUTPUT::

    id : <id_given_in_input>
    result : None if group not exist
             {
               "users_group_id" : "<id>",
               "group_name" :     "<groupname>",
               "active":          "<bool>",
               "members" :  [
                              { 
                                "user_id" :  "<user_id>",
                                "username" : "<username>",
                                "firstname": "<firstname>",
                                "lastname" : "<lastname>",
                                "email" :    "<email>",
                                "emails":    "<list_of_all_additional_emails>",
                                "active" :   "<bool>",
                                "admin" :    "<bool>",
                                "ldap_dn" :  "<ldap_dn>",
                                "last_login": "<last_login>",
                              },
                              …
                            ]
             }
    error : null


get_users_groups
----------------

Lists all existing users groups. This command can be executed only using 
api_key belonging to user with admin rights.


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "get_users_groups"
    args :    { }

OUTPUT::

    id : <id_given_in_input>
    result : [
               {
               "users_group_id" : "<id>",
               "group_name" :     "<groupname>",
               "active":          "<bool>",
               "members" :  [
                              { 
                                "user_id" :  "<user_id>",
                                "username" : "<username>",
                                "firstname": "<firstname>",
                                "lastname" : "<lastname>",
                                "email" :    "<email>",
                                "emails":    "<list_of_all_additional_emails>",
                                "active" :   "<bool>",
                                "admin" :    "<bool>",
                                "ldap_dn" :  "<ldap_dn>",
                                "last_login": "<last_login>",
                              },
                              …
                            ]
               },
               …
              ]
    error : null


create_users_group
------------------

Creates new users group. This command can be executed only using api_key
belonging to user with admin rights


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "create_users_group"
    args:     {
                "group_name":  "<groupname>",
                "active":"<bool> = Optional(True)"
              }

OUTPUT::

    id : <id_given_in_input>
    result: {
              "msg": "created new users group `<groupname>`",
              "users_group": {
                     "users_group_id" : "<id>",
                     "group_name" :     "<groupname>",
                     "active":          "<bool>",
                     "members" :  [
                                  { 
                                    "user_id" :  "<user_id>",
                                    "username" : "<username>",
                                    "firstname": "<firstname>",
                                    "lastname" : "<lastname>",
                                    "email" :    "<email>",
                                    "emails":    "<list_of_all_additional_emails>",
                                    "active" :   "<bool>",
                                    "admin" :    "<bool>",
                                    "ldap_dn" :  "<ldap_dn>",
                                    "last_login": "<last_login>",
                                  },
                                  …
                     ]
               },
            }
    error:  null


add_user_to_users_group
-----------------------

Adds a user to a users group. If user exists in that group success will be 
`false`. This command can be executed only using api_key
belonging to user with admin rights


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "add_user_users_group"
    args:     {
                "usersgroupid" : "<users group id or name>",
                "userid" : "<user_id or username>",
              }

OUTPUT::

    id : <id_given_in_input>
    result: {
              "success": True|False # depends on if member is in group
              "msg": "added member `<username>` to users group `<groupname>` | 
                      User is already in that group"
            }
    error:  null


remove_user_from_users_group
----------------------------

Removes a user from a users group. If user is not in given group success will
be `false`. This command can be executed only 
using api_key belonging to user with admin rights


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "remove_user_from_users_group"
    args:     {
                "usersgroupid" : "<users group id or name>",
                "userid" : "<user_id or username>",
              }

OUTPUT::

    id : <id_given_in_input>
    result: {
              "success":  True|False,  # depends on if member is in group
              "msg": "removed member <username> from users group <groupname> | 
                      User wasn't in group"
            }
    error:  null


get_repo
--------

Gets an existing repository by it's name or repository_id. Members will return
either users_group or user associated to that repository. This command can 
be executed only using api_key belonging to user with admin rights.


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "get_repo"
    args:     {
                "repoid" : "<reponame or repo_id>"
              }

OUTPUT::

    id : <id_given_in_input>
    result: None if repository does not exist or
            {
                "repo_id" :     "<repo_id>",
                "repo_name" :   "<reponame>"
                "repo_type" :   "<repo_type>",
                "clone_uri" :   "<clone_uri>",
                "private": :    "<bool>",
                "created_on" :  "<datetimecreated>",                
                "description" : "<description>",
                "landing_rev":  "<landing_rev>",
                "owner":        "<repo_owner>",
                "fork_of":  "<name_of_fork_parent>",
                "members" :     [
                                  { 
                                    "type": "user",
                                    "user_id" :  "<user_id>",
                                    "username" : "<username>",
                                    "firstname": "<firstname>",
                                    "lastname" : "<lastname>",
                                    "email" :    "<email>",
                                    "emails":    "<list_of_all_additional_emails>",
                                    "active" :   "<bool>",
                                    "admin" :    "<bool>",
                                    "ldap_dn" :  "<ldap_dn>",
                                    "last_login": "<last_login>",
                                    "permission" : "repository.(read|write|admin)"
                                  },
                                  …
                                  { 
                                    "type": "users_group",
                                    "id" :       "<usersgroupid>",
                                    "name" :     "<usersgroupname>",
                                    "active":    "<bool>",
                                    "permission" : "repository.(read|write|admin)"
                                  },
                                  …
                                ]
            }
    error:  null


get_repos
---------

Lists all existing repositories. This command can be executed only using api_key
belonging to user with admin rights


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "get_repos"
    args:     { }

OUTPUT::

    id : <id_given_in_input>
    result: [
              {
                "repo_id" :     "<repo_id>",
                "repo_name" :   "<reponame>"
                "repo_type" :   "<repo_type>",
                "clone_uri" :   "<clone_uri>",
                "private": :    "<bool>",
                "created_on" :  "<datetimecreated>",                
                "description" : "<description>",
                "landing_rev":  "<landing_rev>",
                "owner":        "<repo_owner>",
                "fork_of":  "<name_of_fork_parent>",
              },
              …
            ]
    error:  null


get_repo_nodes
--------------

returns a list of nodes and it's children in a flat list for a given path 
at given revision. It's possible to specify ret_type to show only `files` or 
`dirs`. This command can be executed only using api_key belonging to user 
with admin rights


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "get_repo_nodes"
    args:     {
                "repoid" : "<reponame or repo_id>"
                "revision"  : "<revision>",
                "root_path" : "<root_path>",
                "ret_type"  : "<ret_type> = Optional('all')"
              }

OUTPUT::

    id : <id_given_in_input>
    result: [
              {
                "name" :        "<name>"
                "type" :        "<type>",
              },
              …
            ]
    error:  null


create_repo
-----------

Creates a repository. This command can be executed only using api_key
belonging to user with admin rights.
If repository name contains "/", all needed repository groups will be created.
For example "foo/bar/baz" will create groups "foo", "bar" (with "foo" as parent),
and create "baz" repository with "bar" as group.


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "create_repo"
    args:     {
                "repo_name" :   "<reponame>",
                "owner" :       "<onwer_name_or_id>",
                "repo_type" :   "<repo_type>",
                "description" : "<description> = Optional('')",
                "private" :     "<bool> = Optional(False)",
                "clone_uri" :   "<clone_uri> = Optional(None)",
                "landing_rev" : "<landing_rev> = Optional('tip')",
              }

OUTPUT::

    id : <id_given_in_input>
    result: {
              "msg": "Created new repository `<reponame>`",
              "repo": {
                "repo_id" :     "<repo_id>",
                "repo_name" :   "<reponame>"
                "repo_type" :   "<repo_type>",
                "clone_uri" :   "<clone_uri>",
                "private": :    "<bool>",
                "created_on" :  "<datetimecreated>",                
                "description" : "<description>",
                "landing_rev":  "<landing_rev>",
                "owner":        "<repo_owner>",
                "fork_of":  "<name_of_fork_parent>",
              },
            }
    error:  null


delete_repo
-----------

Deletes a repository. This command can be executed only using api_key
belonging to user with admin rights.


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "delete_repo"
    args:     {
                "repoid" : "<reponame or repo_id>"
              }

OUTPUT::

    id : <id_given_in_input>
    result: {
              "msg": "Deleted repository `<reponame>`",
              "success": true
            }
    error:  null


grant_user_permission
---------------------

Grant permission for user on given repository, or update existing one
if found. This command can be executed only using api_key belonging to user 
with admin rights.


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "grant_user_permission"
    args:     {
                "repoid" : "<reponame or repo_id>"
                "userid" : "<username or user_id>"
                "perm" :       "(repository.(none|read|write|admin))",
              }

OUTPUT::

    id : <id_given_in_input>
    result: {
              "msg" : "Granted perm: `<perm>` for user: `<username>` in repo: `<reponame>`",
              "success": true
            }
    error:  null


revoke_user_permission
----------------------

Revoke permission for user on given repository. This command can be executed 
only using api_key belonging to user with admin rights.


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method  : "revoke_user_permission"
    args:     {
                "repoid" : "<reponame or repo_id>"
                "userid" : "<username or user_id>"
              }

OUTPUT::

    id : <id_given_in_input>
    result: {
              "msg" : "Revoked perm for user: `<username>` in repo: `<reponame>`",
              "success": true
            }
    error:  null


grant_users_group_permission
----------------------------

Grant permission for users group on given repository, or update
existing one if found. This command can be executed only using 
api_key belonging to user with admin rights.


INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method :  "grant_users_group_permission"
    args:     {
                "repoid" : "<reponame or repo_id>"
                "usersgroupid" : "<users group id or name>"
                "perm" : "(repository.(none|read|write|admin))",
              }

OUTPUT::

    id : <id_given_in_input>
    result: {
              "msg" : "Granted perm: `<perm>` for group: `<usersgroupname>` in repo: `<reponame>`",
              "success": true
            }
    error:  null
    
    
revoke_users_group_permission
-----------------------------

Revoke permission for users group on given repository.This command can be 
executed only using api_key belonging to user with admin rights.

INPUT::

    id : <id_for_response>
    api_key : "<api_key>"
    method  : "revoke_users_group_permission"
    args:     {
                "repoid" : "<reponame or repo_id>"
                "usersgroupid" : "<users group id or name>"
              }

OUTPUT::

    id : <id_given_in_input>
    result: {
              "msg" : "Revoked perm for group: `<usersgroupname>` in repo: `<reponame>`",
              "success": true
            }
    error:  null