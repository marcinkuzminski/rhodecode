------------------------------------------------
Pylons based repository management for mercurial
------------------------------------------------

**Overview**

- Has it's own middleware to handle mercurial protocol request. Each request can 
  be logged and authenticated. Runs on threads unlikely to hgweb You can make
  multiple pulls/pushes simultaneous
- Full permissions and authentication per project private/read/write/admin. 
  One account for web interface and mercurial push/pull/clone.
- Mako templates let's you customize look and feel of application.
- Beautiful diffs, annotations and source codes all colored by pygments.
- Mercurial branch graph and yui-flot powered graphs with zooming and statistics
- Admin interface with user/permission management. User activity journal logs
  pulls, pushes, forks,registrations. Possible to disable built in hooks
- Server side forks, it's possible to fork a project and hack it free without
  breaking the main.   
- Full text search on source codes, search on file names. All powered by whoosh
  and build in indexing daemons
  (no external search servers required all in one application)
- Rss / atom feeds, gravatar support, download sources as zip/tarballs  
- Async tasks for speed and performance using celery (works without them too)  
- Backup scripts can do backup of whole app and send it over scp to desired 
  location
- Setup project descriptions and info inside built in db for easy, non 
  file-system operations
- Added cache with invalidation on push/repo management for high performance and
  always up to date data. 
- Based on pylons 1.0 / sqlalchemy 0.6 / sqlite

**Incoming**

- code review based on hg-review (when it's stable)
- git support (when vcs can handle it - almost there !)
- commit based wikis
- clonning from remote repositories into rhodecode (git/mercurial)
- other cools stuff that i can figure out (or You can help me figure out)
   
------------
Installation
------------

**quick setup**
 
- pip install -E rhodecode-venv rhodecode
- activate virtualenv
- run `paster make-config RhodeCode production.ini`
- run `paster setup-app production.ini`
- run `paster runserver production.ini`

You're ready to go.

**MORE DETAILED INSTRUCTIONS**

- I highly recommend to install new virtualenv for rhodecode see 
  http://pypi.python.org/pypi/virtualenv for more details.
- Create new virtualenv using `virtualenv --no-site-packages /var/www/rhodecode-venv`
  this will install new virtual env into /var/www/rhodecode-venv. 
  Activate the virtualenv by running 
  `source activate /var/www/rhodecode-venv/bin/activate`   
- Make a folder for rhodecode somewhere on the filesystem for example /var/www/rhodecode  
- Run easy_install rhodecode
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
- All needed configs are inside rhodecode sources ie. celeryconfig.py, 
  development.ini, production.ini You can configure the email, ports, loggers, 
  workers from there.
- For full text search You can either put crontab entry for 
  `python /var/www/rhodecode/rhodecode/lib/indexers/daemon.py incremental <path_to_repos>`
  or run indexer from admin panel. This will scann the repos given in the 
  application setup or given path for daemon.py and each scann in incremental 
  mode will scann only changed files.