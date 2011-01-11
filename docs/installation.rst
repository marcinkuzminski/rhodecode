.. _installation:

Installation
============

``RhodeCode`` is written entirely in Python, but in order to use it's full
potential there are some third-party requirements. When RhodeCode is used 
together with celery You have to install some kind of message broker,
recommended one is rabbitmq_ to make the async tasks work.

Of course RhodeCode works in sync mode also, then You don't have to install
any third party apps. Celery_ will give You large speed improvement when using
many big repositories. If You plan to use it for 7 or 10 small repositories, it
will work just fine without celery running.
   
After You decide to Run it with celery make sure You run celeryd using paster
and message broker together with the application.   

Install from Cheese Shop
------------------------
Rhodecode requires python 2.x greater than version 2.5

Easiest way to install ``rhodecode`` is to run::

 easy_install rhodecode

Or::

 pip install rhodecode

If you prefer to install manually simply grab latest release from
http://pypi.python.org/pypi/RhodeCode, decompres archive and run::

   python setup.py install


Step by step installation example
---------------------------------


- Assuming You have installed virtualenv_ create one using. 
  The `--no-site-packages` will make sure non of Your system libs are linked 
  with this virtualenv_  

::

 virtualenv --no-site-packages /var/www/rhodecode-venv

- this will install new virtualenv_ into `/var/www/rhodecode-venv`. 
- Activate the virtualenv_ by running 

::

  source /var/www/rhodecode-venv/bin/activate
     
- Make a folder for rhodecode somewhere on the filesystem for example 

::

  mkdir /var/www/rhodecode
  
    
- Run this command to install rhodecode

::

  easy_install rhodecode 

- this will install rhodecode together with pylons
  and all other required python libraries

Requirements for Celery (optional)
----------------------------------

.. note::
   Installing message broker and using celery is optional, RhodeCode will
   work without them perfectly fine.


**Message Broker** 

- preferred is `RabbitMq <http://www.rabbitmq.com/>`_
- possible other is `Redis <http://code.google.com/p/redis/>`_

For installation instructions You can visit: 
http://ask.github.com/celery/getting-started/index.html
It's very nice tutorial how to start celery_ with rabbitmq_


You can now proceed to :ref:`setup`
-----------------------------------



.. _virtualenv: http://pypi.python.org/pypi/virtualenv  
.. _python: http://www.python.org/
.. _mercurial: http://mercurial.selenic.com/
.. _celery: http://celeryproject.org/
.. _rabbitmq: http://www.rabbitmq.com/