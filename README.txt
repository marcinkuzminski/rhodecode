Pylons based replacement for hgwebdir. Fully customizable, 
with authentication, permissions. Based on vcs library.
- has it's own middleware to handle mercurial protocol request each request can
  be logged and authenticated +threaded performance unlikely to hgweb
- mako templates let's you cusmotize look and feel of appplication.
- diffs annotations and source code all colored by pygments.
- admin interface for performing user/permission managments as well as repository
  managment
- added cache with invalidation on push/repo managment for high performance and
  always upto date data.
- rss /atom feed customizable
- future support for git
- based on pylons 1.0 / sqlalchemy 0.6

===
This software is still in beta mode. I don't guarantee that it'll work.
I started this project since i was tired of sad looks, and zero controll over
our company regular hgwebdir.


== INSTALATION
 - create new virtualenv,
 - run python setup.py install
 - goto build/ directory
 - goto pylons_app/lib and run python db_manage.py it should create all 
   needed tables and an admin account. 
 - Edit file repositories.config and change the [paths] where you keep your
   mercurial repositories, remember about permissions for accessing this dir by
   hg app.
 - run paster serve production.ini 
   the app should be available at the 127.0.0.1:8001, the static files should be
   missing since in production.ini sets static_files = false change it to true
   for serving static files in hg app, but i highly recommend to serve 
   statics by proxy (nginx or similar).
 - use admin account you created to login.   