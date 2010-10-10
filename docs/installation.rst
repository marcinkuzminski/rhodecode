.. _installation:

Installation
============

``RhodeCode`` is written entirely in Python, but in order to use it's full
potential there are some third-party requirements. When RhodeCode is used 
together with celery You have to install some kind of message broker,
recommended one is rabbitmq to make the async tasks work.
For installation instructions You can visit: 
http://ask.github.com/celery/getting-started/index.html.

Of course RhodeCode works in sync mode also, then You don't have to install
any third party apps. Celery will give You large speed improvement when using
many big repositories. If You plan to use it for 2 or 3 small repositories, it
will work just fine without celery running.
   
After You decide to Run it with celery make sure You run celeryd and
message broker together with the application.   

Requirements for Celery
-----------------------

**Message Broker** 

- preferred is `RabbitMq <http://www.rabbitmq.com/>`_
- possible other is `Redis <http://code.google.com/p/redis/>`_


Install from Cheese Shop
------------------------

Easiest way to install ``rhodecode`` is to run::

   easy_install rhodecode

Or::

   pip install rhodecode

If you prefer to install manually simply grab latest release from
http://pypi.python.org/pypi/rhodecode, decompres archive and run::

   python setup.py install


**Setting up the application**
I recommend to run the RhodeCode in separate virtualenv.
See http://pypi.python.org/pypi/virtualenv for more details.

- run `paster make-config RhodeCode production.ini` make specific application
  config, 
- run `paster setup-app production.ini` makes the database, and propagates it
  with default data, In this step You have to provide admin username and repositories
  location, it can be a new location or with existing ones in that case RhodeCode
  will scann all new found repos and put it into database.
- run `paster runserver production.ini` runs the server.


**STEP BY STEP EXAMPLE INSTRUCTION**


- Assuming You have setup virtualenv create one using 
  `virtualenv --no-site-packages /var/www/rhodecode-venv`
  this will install new virtual env into /var/www/rhodecode-venv. 
- Activate the virtualenv by running 
  `source activate /var/www/rhodecode-venv/bin/activate`   
- Make a folder for rhodecode somewhere on the filesystem for example 
  /var/www/rhodecode  
- Run easy_install rhodecode, this will install rhodecode together with pylons
  and all other required python libraries
- Run `paster make-config RhodeCode production.ini` in order to install 
  the application config. 
- Run `paster setup-app production.ini` it should create all needed tables 
  and an admin account. Also make sure You specify correct path to repositories.
  You can either use a new location of one with already exising ones. RhodeCode
  will simply add all new found repositories to it's database. 
- Remember that the given path for mercurial repositories must be write 
  accessible for the application. It's very important since RhodeCode web interface
  will work even without such an access but, when trying to do a push it's eventually
  failed with permission denied. 
- Run `paster serve production.ini`
  the app should be available at the 127.0.0.1:5000
- Use admin account you created to login.
- Default permissions on each repository is read, and owner is admin. So remember
  to update these.

- All needed configs are inside rhodecode sources ie. celeryconfig.py, 
  development.ini, production.ini You can configure the email, ports, loggers, 
  workers from there.
- For full text search You can either put crontab entry for 
  `python /var/www/rhodecode/rhodecode/lib/indexers/daemon.py incremental <path_to_repos>`
  or run indexer from admin panel. This will scann the repos given in the 
  application setup or given path for daemon.py and each scann in incremental 
  mode will scan only changed files.