=========
RhodeCode
=========

About
-----

``RhodeCode`` is a fast and powerful management tool for Mercurial_ and GIT_
with a built in push/pull server, full text search and code-review.
It works on http/https and has a built in permission/authentication system with
the ability to authenticate via LDAP or ActiveDirectory. RhodeCode also provides
simple API so it's easy integrable with existing external systems.

RhodeCode is similar in some respects to github_ or bitbucket_,
however RhodeCode can be run as standalone hosted application on your own server.
It is open source and donation ware and focuses more on providing a customized,
self administered interface for Mercurial_ and GIT_  repositories.
RhodeCode works on \*nix systems and Windows it is powered by a vcs_ library
that Lukasz Balcerzak and Marcin Kuzminski created to handle multiple
different version control systems.

RhodeCode uses `PEP386 versioning <http://www.python.org/dev/peps/pep-0386/>`_

Installation
------------
Stable releases of RhodeCode are best installed via::

    easy_install rhodecode

Or::

    pip install rhodecode

Detailed instructions and links may be found on the Installation page.

Please visit http://packages.python.org/RhodeCode/installation.html for
more details

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


RhodeCode Features
------------------

- Has its own middleware to handle mercurial_ and git_ protocol requests.
  Each request is authenticated and logged together with IP address.
- Build for speed and performance. You can make multiple pulls/pushes simultaneous.
  Proven to work with 1000s of repositories and users
- Supports http/https, LDAP, AD, proxy-pass authentication.
- Full permissions (private/read/write/admin) together with IP restrictions for each repository,
  additional explicit forking, repositories group and repository creation permissions.
- User groups for easier permission management.
- Repository groups let you group repos and manage them easier. They come with
  permission delegation features, so you can delegate groups management.
- Users can fork other users repos, and compare them at any time.
- Built in Gist functionality for sharing code snippets.
- Integrates easily with other systems, with custom created mappers you can connect it to almost
  any issue tracker, and with an JSON-RPC API you can make much more
- Build in commit-api let's you add, edit and commit files right from RhodeCode
  web interface using simple editor or upload binary files using simple form.
- Powerfull pull-request driven review system with inline commenting,
  changeset statuses, and notification system.
- Importing and syncing repositories from remote locations for GIT_, Mercurial_ and  SVN.
- Mako templates let's you customize the look and feel of the application.
- Beautiful diffs, annotations and source code browsing all colored by pygments.
  Raw diffs are made in git-diff format for both VCS systems, including GIT_ binary-patches
- Mercurial_ and Git_ DAG graphs and yui-flot powered graphs with zooming and statistics
  to track activity for repositories
- Admin interface with user/permission management. Admin activity journal, logs
  pulls, pushes, forks, registrations and other actions made by all users.
- Server side forks. It is possible to fork a project and modify it freely
  without breaking the main repository.
- rst and markdown README support for repositories.
- Full text search powered by Whoosh on the source files, commit messages, and file names.
  Build in indexing daemons, with optional incremental index build
  (no external search servers required all in one application)
- Setup project descriptions/tags and info inside built in db for easy, non
  file-system operations.
- Intelligent cache with invalidation after push or project change, provides
  high performance and always up to date data.
- RSS / Atom feeds, gravatar support, downloadable sources as zip/tar/gz
- Optional async tasks for speed and performance using celery_
- Backup scripts can do backup of whole app and send it over scp to desired
  location
- Based on pylons / sqlalchemy / sqlite / whoosh / vcs


Incoming / Plans
----------------

- Finer granular permissions per branch, or subrepo
- Web based merges for pull requests
- Tracking history for each lines in files
- Simple issue tracker
- SSH based authentication with server side key management
- Commit based built in wiki system
- More statistics and graph (global annotation + some more statistics)
- Other advancements as development continues (or you can of course make
  additions and or requests)

License
-------

``RhodeCode`` is released under the GPLv3 license.


Getting help
------------

Listed bellow are various support resources that should help.

.. note::

   Please try to read the documentation before posting any issues, especially
   the **troubleshooting section**

- Join the `Google group <http://groups.google.com/group/rhodecode>`_ and ask
  any questions.

- Open an issue at `issue tracker <http://bitbucket.org/marcinkuzminski/rhodecode/issues>`_

- Join #rhodecode on FreeNode (irc.freenode.net)
  or use http://webchat.freenode.net/?channels=rhodecode for web access to irc.

- You can also follow me on twitter **@marcinkuzminski** where i often post some
  news about RhodeCode


Online documentation
--------------------

Online documentation for the current version of RhodeCode is available at
 - http://packages.python.org/RhodeCode/
 - http://rhodecode.readthedocs.org/en/latest/index.html

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
