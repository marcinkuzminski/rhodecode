--------------------------------------------------------------
Pylons based repository management for mercurial (and soon git)
--------------------------------------------------------------

Fully customizable, with authentication, permissions. Based on vcs library.

**Overview**

- has it's own middleware to handle mercurial protocol request each request can 
  be logged and authenticated + threaded performance unlikely to hgweb
- full permissions per project read/write/admin access even on mercurial request
- mako templates let's you customize look and feel of application.
- diffs annotations and source code all colored by pygments.
- mercurial branch graph and yui-flot powered graphs with zooming and statistics
- admin interface for performing user/permission managements as well as repository
  management.
- server side forks, it's possible to fork a project and hack it free without
  breaking the main.   
- full text search of source codes with indexing daemons using whoosh
  (no external search servers required all in one application)
- async tasks for speed and performance using celery (works without them too)  
- Additional settings for mercurial web, (hooks editable from admin
  panel !) also manage paths, archive, remote messages  
- backup scripts can do backup of whole app and send it over scp to desired location
- setup project descriptions and info inside built in db for easy, non 
  file-system operations
- added cache with invalidation on push/repo management for high performance and
  always up to date data. 
- rss / atom feeds, gravatar support
- based on pylons 1.0 / sqlalchemy 0.6

**Incoming**

- code review based on hg-review (when it's stable)
- git support (when vcs can handle it - almost there !)
- commit based wikis
- clonning from remote repositories into rhodecode (git/mercurial)
- other cools stuff that i can figure out (or You can help me figure out)

.. note::
   This software is still in beta mode. 
   I don't guarantee that it'll work correctly.
   

-------------
Installation
-------------

quick setup
 
- pip install -E rhodecode-venv http://bitbucket.org/marcinkuzminski/rhodecode/get/tip.zip
- activate virtualenv
- run `paster make-config RhodeCode production.ini`
- run `paster setup-app production.ini`
- run `paster runserver production.ini`

You're ready to go.


MORE DETAILED INSTRUCTIONS

- I highly recommend to install new virtualenv for rhodecode see 
  http://pypi.python.org/pypi/virtualenv for more details.
- Create new virtualenv using `virtualenv --no-site-packages /var/www/rhodecode-venv`
  this will install new virtual env into /var/www/rhodecode-venv. 
  Activate the virtualenv by running 
  `source activate /var/www/rhodecode-venv/bin/activate`   
- Make a folder for rhodecode somewhere on the filesystem for example /var/www/rhodecode  
- Run easy_install http://bitbucket.org/marcinkuzminski/rhodecode/get/tip.zip.
- Run `paster make-config RhodeCode production.inii` in order to install 
  the application config. You can play with the app settings later 
- Run `paster setup-app production.ini` it should create all needed tables 
  and an admin account make sure You specify correct path to repositories. 
- Remember that the given path for mercurial repositories must be write 
  accessible for the application
- Run paster serve production.ini - or you can use sample init.d scripts.
  the app should be available at the 127.0.0.1:5000
- Use admin account you created to login.
- Default permissions on each repository is read, and owner is admin. So remember
  to update these.
- In order to use full power of async tasks, You must install message broker
  preferably rabbitmq and start celeryd daemon together with rhodecode. 
  The app should gain a lot of speed and become much more responsible. 
  For installation instructions You can visit: 
  http://ask.github.com/celery/getting-started/index.html. 
- All needed configs are inside rhodecode ie. celeryconfig.py , production.ini
  You can configure the email, ports, loggers, workers from there.
- For full text search You can either put crontab entry for 
  `python /var/www/rhodecode/rhodecode/lib/indexers/daemon.py incremental <path_to_repos>`
  or run indexer from admin panel. This will scann the repos given in the 
  application setup or given path for daemon.py and each scann in incremental 
  mode will scann only changed files, 
  Hg Update hook must be activated to index the content it's enabled by default
  after setup