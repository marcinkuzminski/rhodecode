.. _performance:

================================
Optimizing RhodeCode Performance
================================


Follow these few steps to improve performance of RhodeCode system.


1. Increase cache::

    in the .ini file    
    beaker.cache.sql_cache_long.expire=3600 <-- set this to higher number

    This option affects the cache expiration time for main page. Having
    few hundreds of repositories on main page can sometimes make the system
    to behave slow when cache expires for all of them. Increasing `expire`
    option to day (86400) or a week (604800) will improve general response
    times for the main page

2. Switch from sqlite to postgres or mysql
    
    sqlite is a good option when having small load on the system. But due to
    locking issues with sqlite, it's not recommended to use it for larger
    setup. Switching to mysql or postgres will result in a immediate
    performance increase.
    
3. Scale RhodeCode horizontally
    

    - running two or more instances on the same server can speed up things a lot
    - load balance using round robin or ip hash
    - you need to handle consistent user session storage by switching to 
      db sessions, client side sessions or sharing session data folder across 
      instances. See http://beaker.readthedocs.org/ docs for details.
    - remember that each instance needs it's own .ini file and unique
      `instance_id` set in them