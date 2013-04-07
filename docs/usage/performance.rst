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
  increasing cache size (see below), that includes using lightweight dashboard
  option and vcs_full_cache setting in .ini file


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

    Scaling horizontally can give huge performance increase when dealing with
    large traffic (large amount of users, CI servers etc). RhodeCode can be
    scaled horizontally on one (recommended) or multiple machines. In order
    to scale horizontally you need to do the following:

    - each instance needs it's own .ini file and unique `instance_id` set in them
    - each instance `data` storage needs to be configured to be stored on a
      shared disk storage, preferably together with repositories. This `data`
      dir contains template caches, sessions, whoosh index and it's used for
      tasks locking (so it's safe across multiple instances). Set the
      `cache_dir`, `index_dir`, `beaker.cache.data_dir`, `beaker.cache.lock_dir`
      variables in each .ini file to shared location across RhodeCode instances
    - if celery is used each instance should run separate celery instance, but
      the message broken should be common to all of them (ex one rabbitmq
      shared server)
    - load balance using round robin or ip hash, recommended is writing LB rules
      that will separate regular user traffic from automated processes like CI
      servers or build bots.
