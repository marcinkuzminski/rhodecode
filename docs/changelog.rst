.. _changelog:

Changelog
=========

1.0.2 (**2010-11-XX**)
----------------------

- fixed #59 missing graph.js
- fixed repo_size crash when repository had broken symlinks
- fixed python2.5 crashes.
- tested under python2.7
- bumped sqlalcehmy and celery versions

1.0.1 (**2010-11-10**)
----------------------

- fixed #53 python2.5 incompatible enumerate calls
- fixed #52 disable mercurial extension for web
- fixed #51 deleting repositories don't delete it's dependent objects
- small css updated


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
