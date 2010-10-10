.. _index:

Welcome to RhodeCode (RhodiumCode) documentation!
=================================================

``RhodeCode`` is Pylons based repository management and serving for mercurial. 
It's similar to github or bitbucket, but focuses more on closed access restrictions.
There's no default free access to RhodeCode You have to create an account in order
to use the application. 


RhodeCode uses `Semantic Versioning <http://semver.org/>`_

**Features**

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


.. figure::  images/screenshot1_main_page.png
   :align:   left

   Main page of RhodeCode

.. figure::  images/screenshot2_summary_page.png
   :align:   left

   Summary page


**Incoming**

- code review based on hg-review (when it's stable)
- git support (when vcs can handle it - almost there !)
- commit based wikis
- clonning from remote repositories into rhodecode (git/mercurial)
- other cools stuff that i can figure out (or You can help me figure out)

Documentation
=============

**Installation:**

.. toctree::
   :maxdepth: 1

   installation
   setup

Other topics
============

* :ref:`genindex`
* :ref:`search`

.. _python: http://www.python.org/
.. _django: http://www.djangoproject.com/
.. _mercurial: http://mercurial.selenic.com/
.. _subversion: http://subversion.tigris.org/
.. _git: http://git-scm.com/