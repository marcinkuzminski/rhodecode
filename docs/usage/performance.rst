.. _performance:

================================
Optimizing RhodeCode Performance
================================

When serving large amount of big repositories RhodeCode can start
performing slower than expected. Because of demanding nature of handling large
amount of data from version control systems here are some tips how to get
the best performance.

* RhodeCode will perform better on machines with faster disks (SSD/SAN). It's
  more important to have faster disk than faster CPU.

* Slowness on initial page can be easily fixed by grouping repositories, and/or
  increasing cache size (see below)


Follow these few steps to improve performance of RhodeCode system.


1. Increase cache

    in the .ini file::
       
     beaker.cache.sql_cache_long.expire=3600 <-- set this to higher number

    This option affects the cache expiration time for main page. Having
    few hundreds of repositories on main page can sometimes make the system
    to behave slow when cache expires for all of them. Increasing `expire`
    option to day (86400) or a week (604800) will improve general response
    times for the main page. RhodeCode has an intelligent cache expiration
    system and it will expire cache for repositories that had been changed.

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