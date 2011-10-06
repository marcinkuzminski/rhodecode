.. _api:


API
===


Starting from RhodeCode version 1.2 a simple API was implemented.
There's a single schema for calling all api methods. API is implemented
with JSON protocol both ways. An url to send API request in RhodeCode is 
<your_server>/_admin/api


All clients need to send JSON data in such format::

    {
        "api_key":"<api_key>",
        "method":"<method_name>",
        "args":{"<arg_key>":"<arg_val>"}
    }

Example call for autopulling remotes repos using curl::
    curl https://server.com/_admin/api -X POST -H 'content-type:text/plain' --data-binary '{"api_key":"xe7cdb2v278e4evbdf5vs04v832v0efvcbcve4a3","method":"pull","args":{"repo":"CPython"}}'

Simply provide 
 - *api_key* for access and permission validation.
 - *method* is name of method to call
 - *args* is an key:value list of arguments to pass to method
    
.. note::
    
    api_key can be found in your user account page    
    
    
RhodeCode API will return always a JSON formatted answer::
    
    {
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

    api_key:"<api_key>"
    method: "pull"
    args: {"repo":<repo_name>}

OUTPUT::

    result:"Pulled from <repo_name>"
    error:null

    
create_user
-----------

Creates new user in RhodeCode. This command can be executed only using api_key 
belonging to user with admin rights

INPUT::

    api_key:"<api_key>"
    method: "create_user"
    args: {"username": "<username>", 
           "password": "<password>", 
           "active":   "<bool>", 
           "admin":    "<bool>", 
           "name":     "<firstname>", 
           "lastname": "<lastname>", 
           "email":    "<useremail>"}

OUTPUT::

    result:{"id": <newuserid>,
            "msg":"created new user <username>"}
    error:null
    
    
create_users_group
------------------

creates new users group. This command can be executed only using api_key 
belonging to user with admin rights

INPUT::

    api_key:"<api_key>"
    method: "create_user"
    args: {"name":  "<groupname>", 
           "active":"<bool>"}

OUTPUT::

    result:{"id": <newusersgroupid>,
            "msg":"created new users group <groupname>"}
    error:null    
