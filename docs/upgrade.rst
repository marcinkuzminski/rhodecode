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
current config. And tries to do an automerge. It's always better to do a backup
of config file and recheck the content after merge.

It's also good to rebuild the whoosh index since after upgrading the whoosh 
version there could be introduced incompatible index changes.


The last step is to upgrade the database. To do this simply run

::

 paster upgrade-db production.ini
 
This will upgrade schema, as well as update some default on the database,
always recheck the settings of the application, if there are no new options
that need to be set.

.. note::
   Always perform a database backup before doing upgrade.



.. _virtualenv: http://pypi.python.org/pypi/virtualenv  
.. _python: http://www.python.org/
.. _mercurial: http://mercurial.selenic.com/
.. _celery: http://celeryproject.org/
.. _rabbitmq: http://www.rabbitmq.com/