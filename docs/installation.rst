.. _installation:

Installation
============

``RhodeCode`` is written entirely in Python. In order to gain maximum performance
there are some third-party you must install. When RhodeCode is used 
together with celery you have to install some kind of message broker,
recommended one is rabbitmq_ to make the async tasks work.

Of course RhodeCode works in sync mode also and then you do not have to install
any third party applications. However, using Celery_ will give you a large speed improvement when using
many big repositories. If you plan to use RhodeCode for say 7 to 10 small repositories, RhodeCode
will perform perfectly well without celery running.
   
If you make the decision to run RhodeCode with celery make sure you run celeryd using paster
and message broker together with the application.   

Installing RhodeCode from Cheese Shop
-------------------------------------

Rhodecode requires python version 2.5 or higher.

The easiest way to install ``rhodecode`` is to run::

    easy_install rhodecode

Or::

    pip install rhodecode

If you prefer to install RhodeCode manually simply grab latest release from
http://pypi.python.org/pypi/rhodecode, decompress the archive and run::

    python setup.py install


Step by step installation example
---------------------------------


- Assuming you have installed virtualenv_ create a new virtual environment using virtualenv:: 

    virtualenv --no-site-packages /var/www/rhodecode-venv


.. note:: Using ``--no-site-packages`` when generating your
   virtualenv is **very important**. This flag provides the necessary
   isolation for running the set of packages required by
   RhodeCode.  If you do not specify ``--no-site-packages``,
   it's possible that RhodeCode will not install properly into
   the virtualenv, or, even if it does, may not run properly,
   depending on the packages you've already got installed into your
   Python's "main" site-packages dir.


- this will install new virtualenv_ into `/var/www/rhodecode-venv`. 
- Activate the virtualenv_ by running::

    source /var/www/rhodecode-venv/bin/activate

.. note:: If you're using UNIX, *do not* use ``sudo`` to run the
   ``virtualenv`` script.  It's perfectly acceptable (and desirable)
   to create a virtualenv as a normal user.
     
- Make a folder for rhodecode somewhere on the filesystem for example::

    mkdir /var/www/rhodecode
  
    
- Run this command to install rhodecode::

    easy_install rhodecode 

- This will install rhodecode together with pylons and all other required python
  libraries

Requirements for Celery (optional)
----------------------------------

.. note::
   Installing message broker and using celery is optional, RhodeCode will
   work perfectly fine without them.


**Message Broker** 

- preferred is `RabbitMq <http://www.rabbitmq.com/>`_
- A possible alternative is `Redis <http://code.google.com/p/redis/>`_

For installation instructions you can visit: 
http://ask.github.com/celery/getting-started/index.html.
This is a very nice tutorial on how to start using celery_ with rabbitmq_


You can now proceed to :ref:`setup`
-----------------------------------



.. _virtualenv: http://pypi.python.org/pypi/virtualenv  
.. _python: http://www.python.org/
.. _mercurial: http://mercurial.selenic.com/
.. _celery: http://celeryproject.org/
.. _rabbitmq: http://www.rabbitmq.com/