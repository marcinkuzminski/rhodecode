.. _api_key_access:

Access to RhodeCode via API KEY
===============================

Starting from version 1.2 rss/atom feeds and journal feeds
can be accessed via **api_key**. This unique key is automatically generated for
each user in RhodeCode application. Using this key it is possible to access 
feeds without having to log in. When user changes his password a new API KEY
is generated for him automatically. You can check your API KEY in account 
settings page. 