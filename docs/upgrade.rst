.. _upgrade:

Upgrade
=======

Upgrade from Cheese Shop
------------------------

Easiest way to upgrade ``rhodecode`` is to run::

 easy_install -U rhodecode

Or::

 pip install --upgrade rhodecode


Then make sure You run from the installation directory

::
 
 paster make-config RhodeCode production.ini
 
This will display any changes made from new version of RhodeCode To your
current config. And tries to do an automerge.

It's also good to rebuild the whoosh index since after upgrading the whoosh 
versionthere could be introduced incompatible index changes


.. _virtualenv: http://pypi.python.org/pypi/virtualenv  
.. _python: http://www.python.org/
.. _mercurial: http://mercurial.selenic.com/
.. _celery: http://celeryproject.org/
.. _rabbitmq: http://www.rabbitmq.com/