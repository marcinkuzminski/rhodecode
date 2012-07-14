.. _troubleshooting:


===============
Troubleshooting
===============

:Q: **Missing static files?**
:A: Make sure either to set the `static_files = true` in the .ini file or
   double check the root path for your http setup. It should point to 
   for example:
   /home/my-virtual-python/lib/python2.6/site-packages/rhodecode/public
   
| 

:Q: **Can't install celery/rabbitmq?**
:A: Don't worry RhodeCode works without them too. No extra setup is required.
    Try out great celery docs for further help.

|
 
:Q: **Long lasting push timeouts?**
:A: Make sure you set a longer timeouts in your proxy/fcgi settings, timeouts
    are caused by https server and not RhodeCode.
    
| 

:Q: **Large pushes timeouts?**
:A: Make sure you set a proper max_body_size for the http server. Very often
    Apache, Nginx or other http servers kill the connection due to to large
    body.

|

:Q: **Apache doesn't pass basicAuth on pull/push?**
:A: Make sure you added `WSGIPassAuthorization true`.

|

:Q: **Git fails on push/pull?**
:A: Make sure you're using an wsgi http server that can handle chunked encoding
    such as `waitress` or `gunicorn`

|

:Q: **How i use hooks in RhodeCode?**
:A: It's easy if they are python hooks just use advanced link in hooks section
    in Admin panel, that works only for Mercurial. If you want to use githooks,
    just install proper one in repository eg. create file in 
    `/gitrepo/hooks/pre-receive`. You can also use RhodeCode-extensions to
    connect to callback hooks, for both Git and Mercurial.

|

:Q: **RhodeCode is slow for me, how can i make it faster?**
:A: See the :ref:`performance` section

For further questions search the `Issues tracker`_, or post a message in the 
`google group rhodecode`_

.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _python: http://www.python.org/
.. _mercurial: http://mercurial.selenic.com/
.. _celery: http://celeryproject.org/
.. _rabbitmq: http://www.rabbitmq.com/
.. _python-ldap: http://www.python-ldap.org/
.. _mercurial-server: http://www.lshift.net/mercurial-server.html
.. _PublishingRepositories: http://mercurial.selenic.com/wiki/PublishingRepositories
.. _Issues tracker: https://bitbucket.org/marcinkuzminski/rhodecode/issues
.. _google group rhodecode: http://groups.google.com/group/rhodecode