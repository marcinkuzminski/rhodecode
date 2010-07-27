-------------------------------------
Pylons based replacement for hgwebdir
-------------------------------------

Fully customizable, with authentication, permissions. Based on vcs library.

**Overview**

- has it's own middleware to handle mercurial protocol request each request can 
  be logged and authenticated + threaded performance unlikely to hgweb
- full permissions per project read/write/admin access even on mercurial request
- mako templates let's you cusmotize look and feel of appplication.
- diffs annotations and source code all colored by pygments.
- mercurial branch graph and yui-flot powered graphs
- admin interface for performing user/permission managments as well as repository
  managment. Additionall settings for mercurial web, (hooks editable from admin
  panel !) 
- backup scripts can do backup of whole app and send it over scp to desired location
- setup project descriptions and info inside built in db for easy, non 
  file-system operations
- added cache with invalidation on push/repo managment for high performance and
  always upto date data.
- rss /atom feed customizable
- based on pylons 1.0 / sqlalchemy 0.6

**Incoming**

- code review based on hg-review (when it's stable)
- git support (when vcs can handle it)
- other cools stuff that i can figure out
- manage hg ui() per repo, add hooks settings, per repo, and not globally

.. note::
   This software is still in beta mode. I don't guarantee that it'll work.
   

-------------
Installation
-------------
.. note::
   I recomend to install tip version of vcs while the app is in beta mode.
   
   
- create new virtualenv and activate it - highly recommend that you use separate
  virtual-env for whole application
- download hg app from default (not demo) branch from bitbucket and run 
  'python setup.py install' this will install all required dependencies needed
- run paster setup-app production.ini it should create all needed tables 
  and an admin account. 
- remember that the given path for mercurial repositories must be write 
  accessible for the application
- run paster serve development.ini - or you can use manage-hg_app script.
  the app should be available at the 127.0.0.1:5000
- use admin account you created to login.
- default permissions on each repository is read, and owner is admin. So remember
  to update those.
     