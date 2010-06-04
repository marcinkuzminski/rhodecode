------------
Pylons based replacement for hgwebdir
------------

Fully customizable, with authentication, permissions. Based on vcs library.
**Owerview**
- has it's own middleware to handle mercurial protocol request each request can
  be logged and authenticated + threaded performance unlikely to hgweb
- mako templates let's you cusmotize look and feel of appplication.
- diffs annotations and source code all colored by pygments.
- admin interface for performing user/permission managments as well as repository
  managment
- added cache with invalidation on push/repo managment for high performance and
  always upto date data.
- rss /atom feed customizable
- future support for git
- based on pylons 1.0 / sqlalchemy 0.6


**Incoming**
- full permissions per project
- setup project descriptions and info into db
- git support (when vcs can handle it)

.. note::
   This software is still in beta mode. I don't guarantee that it'll work.
   

-------------
Installation
-------------
 - create new virtualenv and activate it
 - download hg app and run python setup.py install 
 - goto build/ directory
 - goto pylons_app/lib and run python db_manage.py it should create all 
   needed tables and an admin account. 
 - edit file repositories.config and change the [paths] where you keep your
   mercurial repositories, remember about permissions for accessing this dir by
   hg app.
 - run paster serve development.ini 
   the app should be available at the 127.0.0.1:5000
 - use admin account you created to login.   