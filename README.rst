
=================================================
Welcome to RhodeCode (RhodiumCode) documentation!
=================================================

``RhodeCode`` (formerly hg-app) is Pylons framework based Mercurial repository 
browser/management with build in push/pull server and full text search.
It works on http/https, has build in permission/authentication(+ldap) features 
It's similar to github or bitbucket, but it's suppose to run as standalone hosted 
application, it's open source and focuses more on restricted access to 
repositories. It's powered by vcs_ library that we created to handle many 
various version control systems.

RhodeCode uses `Semantic Versioning <http://semver.org/>`_

RhodeCode demo
--------------

http://hg.python-works.com

The default access is

- username: demo
- password: demo

Source code
-----------

Source code is along with issue tracker is available at
http://bitbucket.org/marcinkuzminski/rhodecode

Also a source codes can be obtained from demo RhodeCode instance
http://hg.python-works.com/rhodecode/summary

Installation
------------

 Please visit http://packages.python.org/RhodeCode/installation.html


Features
--------

- Has it's own middleware to handle mercurial_ and git_ protocol request. 
  Each request can be logged and authenticated. Runs on threads unlikely to 
  hgweb You can make multiple pulls/pushes simultaneous. Supports http/https
  both on git_ and mercurial_
- Full permissions and authentication per project private/read/write/admin. 
  One account for web interface and mercurial_ push/pull/clone.
- Mako templates let's you customize look and feel of application.
- Beautiful diffs, annotations and source codes all colored by pygments.
- Mercurial_ branch graph and yui-flot powered graphs with zooming and statistics
- Admin interface with user/permission management. User activity journal logs
  pulls, pushes, forks,registrations. Possible to disable built in hooks
- Server side forks, it's possible to fork a project and hack it free without
  breaking the main.   
- Full text search on source codes, search on file names. All powered by whoosh
  and build in indexing daemons
  (no external search servers required all in one application)
- Rss / atom feeds, gravatar support, download sources as zip/tarballs  
- Async tasks for speed and performance using celery_ (works without them too)  
- Backup scripts can do backup of whole app and send it over scp to desired 
  location
- Setup project descriptions and info inside built in db for easy, non 
  file-system operations
- Added cache with invalidation on push/repo management for high performance and
  always up to date data. 
- Based on pylons 1.0 / sqlalchemy 0.6 / sqlite


.. include:: ./docs/screenshots.rst
    
    
Incoming / Plans
----------------

- code review (probably based on hg-review)
- full git_ support, with push/pull server (currently in beta tests)
- project grouping
- redmine integration
- commit based build in wiki system
- clone points and cloning from remote repositories into rhodecode 
  (git_ and mercurial_)
- more statistics and graph (global annotation + some more statistics)
- other cools stuff that i can figure out (or You can help me figure out)

License
-------

``rhodecode`` is released under GPL_ license.


Mailing group Q&A
-----------------

join the `Google group <http://groups.google.com/group/rhodecode>`_

open an issue at `issue tracker <http://bitbucket.org/marcinkuzminski/rhodecode/issues>`_

join #rhodecode on FreeNode (irc.freenode.net)
or use http://webchat.freenode.net/?channels=rhodecode for web access to irc.

Online documentation
--------------------

 Online documentation for current version is available at
 http://packages.python.org/RhodeCode/.
 You may also build documentation for yourself - go into ``docs/`` and run::

   make html

