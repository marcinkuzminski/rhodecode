.. _api:


API
===


Starting from RhodeCode version 1.2 a simple API was implemented.
There's one schema for calling all api methods. API is implemented
with JSON protocol both ways. 


Clients need to send JSON data in such format::

    {
        "api_key":"<api_key>",
        "method":"<method_name>",
        "args":{"<arg_key>":"<arg_val>"}
    }

Simply provide api_key for access and permission validation
method is name of method to call
and args is an key:value list of arguments to pass to method
    
.. note::
    
    api_key can be found in your user account page    
    
    
And will receive JSON formatted answer::
    
    {
        "result": "<result>", 
        "error": null
    }

All responses from API will be `HTTP/1.0 200 OK`, if there's an error while
calling api **error** key from response will contain failure description 
and result will be null.

API METHODS
+++++++++++

    
pull
----

Pulls given repo from remote location. Can be used to automatically keep 
remote repos upto date. This command can be executed only using admin users
api_key

::
    
    method: "pull"
    args: {"repo":<repo_name>}

