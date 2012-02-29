.. _upgrade:

Upgrade
=======

Upgrading from Cheese Shop
--------------------------

.. note::
   Firstly, it is recommended that you **always** perform a database backup 
   before doing an upgrade.

The easiest way to upgrade ``rhodecode`` is to run::

 easy_install -U rhodecode

Or::

 pip install --upgrade rhodecode


Then make sure you run the following command from the installation directory::
 
 paster make-config RhodeCode production.ini
 
This will display any changes made by the new version of RhodeCode to your
current configuration. It will try to perform an automerge. It's always better
to make a backup of your configuration file before hand and recheck the 
content after the automerge.

.. note::
   Please always make sure your .ini files are upto date. Often errors are
   caused by missing params added in new versions.


It is also recommended that you rebuild the whoosh index after upgrading since 
the new whoosh version could introduce some incompatible index changes. Please
Read the changelog to see if there were any changes to whoosh.


The final step is to upgrade the database. To do this simply run::

    paster upgrade-db production.ini
 
This will upgrade the schema and update some of the defaults in the database,
and will always recheck the settings of the application, if there are no new 
options that need to be set.


.. _virtualenv: http://pypi.python.org/pypi/virtualenv  
.. _python: http://www.python.org/
.. _mercurial: http://mercurial.selenic.com/
.. _celery: http://celeryproject.org/
.. _rabbitmq: http://www.rabbitmq.com/