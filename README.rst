
=================================================
Welcome to RhodeCode (RhodiumCode) documentation!
=================================================

``RhodeCode`` (formerly hg-app) is Pylons framework based Mercurial repository 
browser/management with build in push/pull server and full text search.
It works on http/https, has build in permission/authentication(+ldap) features 
It's similar to github or bitbucket, but it's suppose to run as standalone 
hosted application, it's open source and focuses more on restricted access to 
repositories. It's powered by vcs_ library that me na Lukasz Balcerzak created 
to handle many various version control systems.

RhodeCode uses `Semantic Versioning <http://semver.org/>`_

RhodeCode demo
--------------

http://hg.python-works.com

The default access is anonymous but You can login to administrative account
using those credentials

- username: demo
- password: demo

Source code
-----------

The most up to date sources can be obtained from my own RhodeCode instance
https://rhodecode.org 

Rarely updated source code and issue tracker is available at bitbcuket
http://bitbucket.org/marcinkuzminski/rhodecode

Installation
------------

 Please visit http://packages.python.org/RhodeCode/installation.html


Features
--------

- Has it's own middleware to handle mercurial_ protocol request. 
  Each request can be logged and authenticated. Runs on threads unlikely to 
  hgweb. You can make multiple pulls/pushes simultaneous. Supports http/https 
  and ldap
- Full permissions (private/read/write/admin) and authentication per project. 
  One account for web interface and mercurial_ push/pull/clone operations.
- Mako templates let's you customize look and feel of application.
- Beautiful diffs, annotations and source codes all colored by pygments.
- Mercurial_ branch graph and yui-flot powered graphs with zooming and statistics
- Admin interface with user/permission management. Admin activity journal, logs
  pulls, pushes, forks, registrations and other actions made by all users.
- Server side forks, it's possible to fork a project and hack it free without
  breaking the main repository.
- Full text search powered by Whoosh on source codes, and file names.
  Build in indexing daemons, with optional incremental index build
  (no external search servers required all in one application)
- Setup project descriptions and info inside built in db for easy, non 
  file-system operations
- Inteligent cache with invalidation after push or project change, provides high 
  performance and always up to date data.    
- Rss / atom feeds, gravatar support, download sources as zip/tar/gz
- Async tasks for speed and performance using celery_ (works without them too)  
- Backup scripts can do backup of whole app and send it over scp to desired 
  location 
- Based on pylons / sqlalchemy / sqlite / whoosh / vcs


.. include:: ./docs/screenshots.rst
    
    
Incoming / Plans
----------------

- project grouping
- User groups/teams
- code review (probably based on hg-review)
- full git_ support, with push/pull server (currently in beta tests)
- redmine integration
- public accessible activity feeds
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

