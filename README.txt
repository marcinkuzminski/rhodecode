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
run dbmanage.py from pylons_app/lib it should create all needed table and
an admin account, Edit file repositories.config and change the path for you 
mercurial repositories, remember about permissions.