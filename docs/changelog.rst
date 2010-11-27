.. _changelog:

Changelog
=========

1.1.0 (**2010-XX-XX**)
----------------------

:status: in-progress
:branch: beta

news
++++

- rewrite of internals for vcs >=0.1.10
- anonymous access, authentication via ldap
- performance upgrade for cached repos list - each repository has it's own 
  cache that's invalidated when needed.
- main page quick filter for filtering repositories
- user dashboards with ability to follow chosen repositories actions
- sends email to admin on new user registration
- added cache/statistics reset options into repository settings
- more detailed action logger (based on hooks) with pushed changesets lists
  and options to disable those hooks from admin panel
- introduced new enhanced changelog for merges that shows more accurate results
- gui optimizations, fixed application width to 1024px
- whoosh, celeryd, upgrade moved to paster command

fixes
+++++

- fixes #61 forked repo was showing only after cache expired
- fixes #76 no confirmation on user deletes
- fixes #66 Name field misspelled
- fixes #72 block user removal when he owns repositories
- fixes #69 added password confirmation fields
- numerous small bugfixes
- a lot of fixes and tweaks for file browser
- fixed detached session issues

(special thanks for TkSoh for detailed feedback)


1.0.2 (**2010-11-12**)
----------------------

news
++++

- tested under python2.7
- bumped sqlalchemy and celery versions

fixes
+++++

- fixed #59 missing graph.js
- fixed repo_size crash when repository had broken symlinks
- fixed python2.5 crashes.


1.0.1 (**2010-11-10**)
----------------------

news
++++

- small css updated

fixes
+++++

- fixed #53 python2.5 incompatible enumerate calls
- fixed #52 disable mercurial extension for web
- fixed #51 deleting repositories don't delete it's dependent objects


1.0.0 (**2010-11-02**)
----------------------

- security bugfix simplehg wasn't checking for permissions on commands
  other than pull or push.
- fixed doubled messages after push or pull in admin journal
- templating and css corrections, fixed repo switcher on chrome, updated titles
- admin menu accessible from options menu on repository view
- permissions cached queries

1.0.0rc4  (**2010-10-12**)
--------------------------

- fixed python2.5 missing simplejson imports (thanks to Jens Bäckman)
- removed cache_manager settings from sqlalchemy meta
- added sqlalchemy cache settings to ini files
- validated password length and added second try of failure on paster setup-app
- fixed setup database destroy prompt even when there was no db


1.0.0rc3 (**2010-10-11**)
-------------------------

- fixed i18n during installation.

1.0.0rc2 (**2010-10-11**)
-------------------------

- Disabled dirsize in file browser, it's causing nasty bug when dir renames 
  occure. After vcs is fixed it'll be put back again.
- templating/css rewrites, optimized css.

