.. _api:


API
===


Starting from RhodeCode version 1.2 a simple API was implemented.
There's a single schema for calling all api methods. API is implemented
with JSON protocol both ways. An url to send API request in RhodeCode is
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
        "id:<id>,
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
        "id":<id>,
        "result": "<result>",
        "error": null
    }

All responses from API will be `HTTP/1.0 200 OK`, if there's an error while
calling api *error* key from response will contain failure description
and result will be null.

API METHODS
+++++++++++


pull
----

Pulls given repo from remote location. Can be used to automatically keep
remote repos up to date. This command can be executed only using api_key
belonging to user with admin rights

INPUT::

    api_key : "<api_key>"
    method :  "pull"
    args :    {
                "repo_name" : "<reponame>"
              }

OUTPUT::

    result : "Pulled from <reponame>"
    error :  null


get_user
--------

Get's an user by username or user_id, Returns empty result if user is not found.
This command can be executed only using api_key belonging to user with admin 
rights.


INPUT::

    api_key : "<api_key>"
    method :  "get_user"
    args :    { 
                "userid" : "<username or user_id>"
              }

OUTPUT::

    result: None if user does not exist or 
            {
                "id" :       "<id>",
                "username" : "<username>",
                "firstname": "<firstname>",
                "lastname" : "<lastname>",
                "email" :    "<email>",
                "active" :   "<bool>",
                "admin" :    "<bool>",
                "ldap_dn" :  "<ldap_dn>"
            }

    error:  null


get_users
---------

Lists all existing users. This command can be executed only using api_key
belonging to user with admin rights.


INPUT::

    api_key : "<api_key>"
    method :  "get_users"
    args :    { }

OUTPUT::

    result: [
              {
                "id" :       "<id>",
                "username" : "<username>",
                "firstname": "<firstname>",
                "lastname" : "<lastname>",
                "email" :    "<email>",
                "active" :   "<bool>",
                "admin" :    "<bool>",
                "ldap_dn" :  "<ldap_dn>"
              },
    	      …
            ]
    error:  null


create_user
-----------

Creates new user. This command can 
be executed only using api_key belonging to user with admin rights.


INPUT::

    api_key : "<api_key>"
    method :  "create_user"
    args :    {
                "username" :  "<username>",
                "password" :  "<password>",
                "email" :     "<useremail>",
                "firstname" : "<firstname> = None",
                "lastname" :  "<lastname> = None",
                "active" :    "<bool> = True",
                "admin" :     "<bool> = False",
                "ldap_dn" :   "<ldap_dn> = None"
              }

OUTPUT::

    result: {
              "id" : "<new_user_id>",
              "msg" : "created new user <username>"
            }
    error:  null


update_user
-----------

updates current one if such user exists. This command can 
be executed only using api_key belonging to user with admin rights.


INPUT::

    api_key : "<api_key>"
    method :  "update_user"
    args :    {
                "userid" : "<user_id or username>",
                "username" :  "<username>",
                "password" :  "<password>",
                "email" :     "<useremail>",
                "firstname" : "<firstname>",
                "lastname" :  "<lastname>",
                "active" :    "<bool>",
                "admin" :     "<bool>",
                "ldap_dn" :   "<ldap_dn>"
              }

OUTPUT::

    result: {
              "id" : "<edited_user_id>",
              "msg" : "updated user <username>"
            }
    error:  null


get_users_group
---------------

Gets an existing users group. This command can be executed only using api_key
belonging to user with admin rights.


INPUT::

    api_key : "<api_key>"
    method :  "get_users_group"
    args :    {
                "group_name" : "<name>"
              }

OUTPUT::

    result : None if group not exist
             {
               "id" :         "<id>",
               "group_name" : "<groupname>",
               "active":      "<bool>",
               "members" :  [
                              { "id" :       "<userid>",
                                "username" : "<username>",
                                "firstname": "<firstname>",
                                "lastname" : "<lastname>",
                                "email" :    "<email>",
                                "active" :   "<bool>",
                                "admin" :    "<bool>",
                                "ldap" :     "<ldap_dn>"
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

    api_key : "<api_key>"
    method :  "get_users_groups"
    args :    { }

OUTPUT::

    result : [
               {
                 "id" :         "<id>",
                 "group_name" : "<groupname>",
                 "active":      "<bool>",
                 "members" :  [
	    	                    {
	    	                      "id" :       "<userid>",
	                              "username" : "<username>",
	                              "firstname": "<firstname>",
	                              "lastname" : "<lastname>",
	                              "email" :    "<email>",
	                              "active" :   "<bool>",
	                              "admin" :    "<bool>",
	                              "ldap" :     "<ldap_dn>"
	                            },
	    	                    …
	                          ]
	            }
              ]
    error : null


create_users_group
------------------

Creates new users group. This command can be executed only using api_key
belonging to user with admin rights


INPUT::

    api_key : "<api_key>"
    method :  "create_users_group"
    args:     {
                "group_name":  "<groupname>",
                "active":"<bool> = True"
              }

OUTPUT::

    result: {
              "id":  "<newusersgroupid>",
              "msg": "created new users group <groupname>"
            }
    error:  null


add_user_to_users_group
-----------------------

Adds a user to a users group. If user exists in that group success will be 
`false`. This command can be executed only using api_key
belonging to user with admin rights


INPUT::

    api_key : "<api_key>"
    method :  "add_user_users_group"
    args:     {
                "group_name" :  "<groupname>",
                "username" :   "<username>"
              }

OUTPUT::

    result: {
              "id":  "<newusersgroupmemberid>",
              "success": True|False # depends on if member is in group
              "msg": "added member <username> to users group <groupname> | 
                      User is already in that group"
            }
    error:  null


remove_user_from_users_group
----------------------------

Removes a user from a users group. If user is not in given group success will
be `false`. This command can be executed only 
using api_key belonging to user with admin rights


INPUT::

    api_key : "<api_key>"
    method :  "remove_user_from_users_group"
    args:     {
                "group_name" :  "<groupname>",
                "username" :   "<username>"
              }

OUTPUT::

    result: {
              "success":  True|False,  # depends on if member is in group
              "msg": "removed member <username> from users group <groupname> | 
                      User wasn't in group"
            }
    error:  null


get_repo
--------

Gets an existing repository by it's name or repository_id. This command can 
be executed only using api_key belonging to user with admin rights.


INPUT::

    api_key : "<api_key>"
    method :  "get_repo"
    args:     {
                "repoid" : "<reponame or repo_id>"
              }

OUTPUT::

    result: None if repository does not exist or
            {
                "id" :          "<id>",
                "repo_name" :   "<reponame>"
                "type" :        "<type>",
                "description" : "<description>",
                "members" :     [
                                  { "id" :         "<userid>",
                                    "username" :   "<username>",
                                    "firstname":   "<firstname>",
                                    "lastname" :   "<lastname>",
                                    "email" :      "<email>",
                                    "active" :     "<bool>",
                                    "admin" :      "<bool>",
                                    "ldap" :       "<ldap_dn>",
                                    "permission" : "repository.(read|write|admin)"
                                  },
                                  …
                                  {
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

    api_key : "<api_key>"
    method :  "get_repos"
    args:     { }

OUTPUT::

    result: [
              {
                "id" :          "<id>",
                "repo_name" :   "<reponame>"
                "type" :        "<type>",
                "description" : "<description>"
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

    api_key : "<api_key>"
    method :  "get_repo_nodes"
    args:     {
                "repo_name" : "<reponame>",
                "revision"  : "<revision>",
                "root_path" : "<root_path>",
                "ret_type"  : "<ret_type>" = 'all'
              }

OUTPUT::

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

    api_key : "<api_key>"
    method :  "create_repo"
    args:     {
                "repo_name" :   "<reponame>",
                "owner_name" :  "<ownername>",
                "description" : "<description> = ''",
                "repo_type" :   "<type> = 'hg'",
                "private" :     "<bool> = False",
                "clone_uri" :   "<clone_uri> = None",
              }

OUTPUT::

    result: {
              "id": "<newrepoid>",
              "msg": "Created new repository <reponame>",
            }
    error:  null


delete_repo
-----------

Deletes a repository. This command can be executed only using api_key
belonging to user with admin rights.


INPUT::

    api_key : "<api_key>"
    method :  "delete_repo"
    args:     {
                "repo_name" :   "<reponame>",
              }

OUTPUT::

    result: {
              "msg": "Deleted repository <reponame>",
            }
    error:  null


grant_user_permission
---------------------

Grant permission for user on given repository, or update existing one
if found. This command can be executed only using api_key belonging to user 
with admin rights.


INPUT::

    api_key : "<api_key>"
    method :  "grant_user_permission"
    args:     {
                "repo_name" :  "<reponame>",
                "username" :   "<username>",
                "perm" :       "(repository.(none|read|write|admin))",
              }

OUTPUT::

    result: {
              "msg" : "Granted perm: <perm> for user: <username> in repo: <reponame>"
            }
    error:  null


revoke_user_permission
----------------------

Revoke permission for user on given repository. This command can be executed 
only using api_key belonging to user with admin rights.


INPUT::

    api_key : "<api_key>"
    method  : "revoke_user_permission"
    args:     {
                "repo_name" :  "<reponame>",
                "username" :   "<username>",
              }

OUTPUT::

    result: {
              "msg" : "Revoked perm for user: <suername> in repo: <reponame>"
            }
    error:  null


grant_users_group_permission
----------------------------

Grant permission for users group on given repository, or update
existing one if found. This command can be executed only using 
api_key belonging to user with admin rights.


INPUT::

    api_key : "<api_key>"
    method :  "grant_users_group_permission"
    args:     {
                "repo_name" : "<reponame>",
                "group_name" : "<usersgroupname>",
                "perm" : "(repository.(none|read|write|admin))",
              }

OUTPUT::

    result: {
              "msg" : "Granted perm: <perm> for group: <usersgroupname> in repo: <reponame>"
            }
    error:  null
    
    
revoke_users_group_permission
-----------------------------

Revoke permission for users group on given repository.This command can be 
executed only using api_key belonging to user with admin rights.

INPUT::

    api_key : "<api_key>"
    method  : "revoke_users_group_permission"
    args:     {
                "repo_name" :  "<reponame>",
                "users_group" :   "<usersgroupname>",
              }

OUTPUT::

    result: {
              "msg" : "Revoked perm for group: <usersgroupname> in repo: <reponame>"
            }
    error:  null