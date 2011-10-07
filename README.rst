=================================================
Welcome to RhodeCode (RhodiumCode) documentation!
=================================================

``RhodeCode`` is a Pylons framework based Mercurial repository 
browser/management tool with a built in push/pull server and full text search.
It works on http/https and has a built in permission/authentication system with 
the ability to authenticate via LDAP or ActiveDirectory. RhodeCode also supports
simple API so it's easy integrable with existing systems.

RhodeCode is similar in some respects to github or bitbucket_, 
however RhodeCode can be run as standalone hosted application on your own server.  
It is open source and donation ware and focuses more on providing a customized, 
self administered interface for Mercurial(and soon GIT) repositories. 
RhodeCode is powered by a vcs_ library that Lukasz Balcerzak and I created to 
handle multiple different version control systems.

RhodeCode uses `Semantic Versioning <http://semver.org/>`_

RhodeCode demo
--------------

http://demo.rhodecode.org

The default access is anonymous but you can login to an administrative account
using the following credentials:

- username: demo
- password: demo12

Source code
-----------

The latest sources can be obtained from official RhodeCode instance
https://secure.rhodecode.org 


MIRRORS:

Issue tracker and sources at bitbucket_

http://bitbucket.org/marcinkuzminski/rhodecode

Sources at github_

https://github.com/marcinkuzminski/rhodecode

Installation
------------

Please visit http://packages.python.org/RhodeCode/installation.html


RhodeCode Features
------------------

- Has it's own middleware to handle mercurial_ protocol requests. 
  Each request can be logged and authenticated.
- Runs on threads unlike hgweb. You can make multiple pulls/pushes simultaneous.
  Supports http/https and LDAP
- Full permissions (private/read/write/admin) and authentication per project. 
  One account for web interface and mercurial_ push/pull/clone operations.
- Have built in users groups for easier permission management
- Repository groups let you group repos and manage them easier.
- Users can fork other users repo. RhodeCode have also compare view to see
  combined changeset for all changeset made within single push.
- Build in commit-api let's you add, edit and commit files right from RhodeCode
  interface using simple editor or upload form for binaries.
- Mako templates let's you customize the look and feel of the application.
- Beautiful diffs, annotations and source code browsing all colored by pygments. 
  Raw diffs are made in git-diff format, including git_ binary-patches
- Mercurial_ branch graph and yui-flot powered graphs with zooming and statistics
- Admin interface with user/permission management. Admin activity journal, logs
  pulls, pushes, forks, registrations and other actions made by all users.
- Server side forks. It is possible to fork a project and modify it freely 
  without breaking the main repository. You can even write Your own hooks 
  and install them
- Full text search powered by Whoosh on the source files, and file names.
  Build in indexing daemons, with optional incremental index build
  (no external search servers required all in one application)
- Setup project descriptions and info inside built in db for easy, non 
  file-system operations
- Intelligent cache with invalidation after push or project change, provides 
  high performance and always up to date data.
- Rss / atom feeds, gravatar support, download sources as zip/tar/gz
- Async tasks for speed and performance using celery_ (works without them too)  
- Backup scripts can do backup of whole app and send it over scp to desired 
  location 
- Based on pylons / sqlalchemy / sqlite / whoosh / vcs


.. include:: ./docs/screenshots.rst
    
    
Incoming / Plans
----------------

- Finer granular permissions per branch, repo group or subrepo
- pull requests and web based merges
- notification and message system 
- SSH based authentication with server side key management
- Code review (probably based on hg-review)
- Full git_ support, with push/pull server (currently in beta tests)
- Redmine and other bugtrackers integration
- Commit based built in wiki system
- More statistics and graph (global annotation + some more statistics)
- Other advancements as development continues (or you can of course make 
  additions and or requests)

License
-------

``RhodeCode`` is released under the GPLv3 license.


Mailing group Q&A
-----------------

Join the `Google group <http://groups.google.com/group/rhodecode>`_

Open an issue at `issue tracker <http://bitbucket.org/marcinkuzminski/rhodecode/issues>`_

Join #rhodecode on FreeNode (irc.freenode.net)
or use http://webchat.freenode.net/?channels=rhodecode for web access to irc.

Online documentation
--------------------

Online documentation for the current version of RhodeCode is available at
http://packages.python.org/RhodeCode/.
You may also build the documentation for yourself - go into ``docs/`` and run::

   make html

(You need to have sphinx_ installed to build the documentation. If you don't
have sphinx_ installed you can install it via the command: 
``easy_install sphinx``)
 
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _python: http://www.python.org/
.. _sphinx: http://sphinx.pocoo.org/
.. _mercurial: http://mercurial.selenic.com/
.. _bitbucket: http://bitbucket.org/
.. _github: http://github.com/
.. _subversion: http://subversion.tigris.org/
.. _git: http://git-scm.com/
.. _celery: http://celeryproject.org/
.. _Sphinx: http://sphinx.pocoo.org/
.. _vcs: http://pypi.python.org/pypi/vcs