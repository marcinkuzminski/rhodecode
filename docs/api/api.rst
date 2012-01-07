.. _api:


API
===


Starting from RhodeCode version 1.2 a simple API was implemented.
There's a single schema for calling all api methods. API is implemented
with JSON protocol both ways. An url to send API request in RhodeCode is
<your_server>/_admin/api

API ACCESS FOR WEB VIEWS
++++++++++++++++++++++++

API access can also be turned on for each view decorated with `@LoginRequired`
decorator. To enable API access simple change standard login decorator into
`@LoginRequired(api_access=True)`. After such a change view can be accessed
by adding a GET parameter to url `?api_key=<api_key>`. By default it's only
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

Get's an user by username, Returns empty result if user is not found.
This command can be executed only using api_key belonging to user with admin 
rights.

INPUT::

    api_key : "<api_key>"
    method :  "get_user"
    args :    { 
                "username" : "<username>"
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
                "ldap" :     "<ldap_dn>"
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
                "ldap" :     "<ldap_dn>"
              },
    	      …
            ]
    error:  null

create_user
-----------

Creates new user in RhodeCode. This command can be executed only using api_key
belonging to user with admin rights.

INPUT::

    api_key : "<api_key>"
    method :  "create_user"
    args :    {
                "username" :  "<username>",
                "password" :  "<password>",
                "firstname" : "<firstname>",
                "lastname" :  "<lastname>",
                "email" :     "<useremail>"
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

Adds a user to a users group. This command can be executed only using api_key
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
              "msg": "created new users group member"
            }
    error:  null

get_repo
--------

Gets an existing repository. This command can be executed only using api_key
belonging to user with admin rights

INPUT::

    api_key : "<api_key>"
    method :  "get_repo"
    args:     {
                "repo_name" : "<reponame>"
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
                "private" :     "<bool> = False"
              }

OUTPUT::

    result: {
                "id": "<newrepoid>",
                "msg": "Created new repository <reponame>",
            }
    error:  null

add_user_to_repo
----------------

Add a user to a repository. This command can be executed only using api_key
belonging to user with admin rights.
If "perm" is None, user will be removed from the repository.

INPUT::

    api_key : "<api_key>"
    method :  "add_user_to_repo"
    args:     {
                "repo_name" :  "<reponame>",
                "username" :   "<username>",
                "perm" :       "(None|repository.(read|write|admin))",
              }

OUTPUT::

    result: {
                "msg" : "Added perm: <perm> for <username> in repo: <reponame>"
            }
    error:  null

add_users_group_to_repo
-----------------------

Add a users group to a repository. This command can be executed only using 
api_key belonging to user with admin rights. If "perm" is None, group will 
be removed from the repository.

INPUT::

    api_key : "<api_key>"
    method :  "add_users_group_to_repo"
    args:     {
                "repo_name" :  "<reponame>",
                "group_name" : "<groupname>",
                "perm" :       "(None|repository.(read|write|admin))",
              }
OUTPUT::
    
    result: {
                "msg" : Added perm: <perm> for <groupname> in repo: <reponame>"
            }

