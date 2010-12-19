.. _setup:

Setup
=====


Setting up the application
--------------------------

First You'll ned to create RhodeCode config file. Run the following command 
to do this

::
 
 paster make-config RhodeCode production.ini

- This will create `production.ini` config inside the directory
  this config contains various settings for RhodeCode, e.g proxy port, 
  email settings, usage of static files, cache, celery settings and logging.



Next we need to create the database.

::

 paster setup-app production.ini

- This command will create all needed tables and an admin account. 
  When asked for a path You can either use a new location of one with already 
  existing ones. RhodeCode will simply add all new found repositories to 
  it's database. Also make sure You specify correct path to repositories.
- Remember that the given path for mercurial_ repositories must be write 
  accessible for the application. It's very important since RhodeCode web 
  interface will work even without such an access but, when trying to do a 
  push it'll eventually fail with permission denied errors. 

You are ready to use rhodecode, to run it simply execute

::
 
 paster serve production.ini
 
- This command runs the RhodeCode server the app should be available at the 
  127.0.0.1:5000. This ip and port is configurable via the production.ini 
  file created in previous step
- Use admin account you created to login.
- Default permissions on each repository is read, and owner is admin. So 
  remember to update these if needed. In the admin panel You can toggle ldap,
  anonymous, permissions settings. As well as edit more advanced options on 
  users and repositories
  
    
Setting up Whoosh full text search
----------------------------------

Index for whoosh can be build starting from version 1.1 using paster command
passing repo locations to index, as well as Your config file that stores
whoosh index files locations. There is possible to pass `-f` to the options
to enable full index rebuild. Without that indexing will run always in in
incremental mode.

::

 paster make-index production.ini --repo-location=<location for repos> 

for full index rebuild You can use

::

 paster make-index production.ini -f --repo-location=<location for repos>

- For full text search You can either put crontab entry for

This command can be run even from crontab in order to do periodical 
index builds and keep Your index always up to date. An example entry might 
look like this

::
 
 /path/to/python/bin/paster /path/to/rhodecode/production.ini --repo-location=<location for repos> 
  
When using incremental(default) mode whoosh will check last modification date 
of each file and add it to reindex if newer file is available. Also indexing 
daemon checks for removed files and removes them from index. 

Sometime You might want to rebuild index from scratch. You can do that using 
the `-f` flag passed to paster command or, in admin panel You can check 
`build from scratch` flag.


Setting up LDAP support
-----------------------

RhodeCode starting from version 1.1 supports ldap authentication. In order
to use ldap, You have to install python-ldap package. This package is available
via pypi, so You can install it by running

::

 easy_install python-ldap
 
::

 pip install python-ldap

.. note::
   python-ldap requires some certain libs on Your system, so before installing 
   it check that You have at least `openldap`, and `sasl` libraries.

ldap settings are located in admin->ldap section,

Here's a typical ldap setup::

 Enable ldap  = checked                 #controls if ldap access is enabled
 Host         = host.domain.org         #actual ldap server to connect
 Port         = 389 or 689 for ldaps    #ldap server ports
 Enable LDAPS = unchecked               #enable disable ldaps
 Account      = <account>               #access for ldap server(if required)
 Password     = <password>              #password for ldap server(if required)
 Base DN      = uid=%(user)s,CN=users,DC=host,DC=domain,DC=org
 

`Account` and `Password` are optional, and used for two-phase ldap 
authentication so those are credentials to access Your ldap, if it doesn't 
support anonymous search/user lookups. 

Base DN must have %(user)s template inside, it's a placer where Your uid used
to login would go, it allows admins to specify not standard schema for uid 
variable

If all data are entered correctly, and `python-ldap` is properly installed
Users should be granted to access RhodeCode wit ldap accounts. When 
logging at the first time an special ldap account is created inside RhodeCode, 
so You can control over permissions even on ldap users. If such user exists 
already in RhodeCode database ldap user with the same username would be not 
able to access RhodeCode.

If You have problems with ldap access and believe You entered correct 
information check out the RhodeCode logs,any error messages sent from 
ldap will be saved there.



Setting Up Celery
-----------------

Since version 1.1 celery is configured by the rhodecode ini configuration files
simply set use_celery=true in the ini file then add / change the configuration 
variables inside the ini file.

Remember that the ini files uses format with '.' not with '_' like celery
so for example setting `BROKER_HOST` in celery means setting `broker.host` in
the config file.

In order to make start using celery run::
 paster celeryd <configfile.ini>



.. note::
   Make sure You run this command from same virtualenv, and with the same user
   that rhodecode runs.


Nginx virtual host example
--------------------------

Sample config for nginx using proxy::

 server {
    listen          80;
    server_name     hg.myserver.com;
    access_log      /var/log/nginx/rhodecode.access.log;
    error_log       /var/log/nginx/rhodecode.error.log;
    location / {
            root /var/www/rhodecode/rhodecode/public/;
            if (!-f $request_filename){
                proxy_pass      http://127.0.0.1:5000;
            }
            #this is important for https !!!
            proxy_set_header X-Url-Scheme $scheme;
            include         /etc/nginx/proxy.conf;  
    }
 }  
  
Here's the proxy.conf. It's tuned so it'll not timeout on long
pushes and also on large pushes::

    proxy_redirect              off;
    proxy_set_header            Host $host;
    proxy_set_header            X-Host $http_host;
    proxy_set_header            X-Real-IP $remote_addr;
    proxy_set_header            X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header            Proxy-host $proxy_host;
    client_max_body_size        400m;
    client_body_buffer_size     128k;
    proxy_buffering             off;
    proxy_connect_timeout       3600;
    proxy_send_timeout          3600;
    proxy_read_timeout          3600;
    proxy_buffer_size           8k;
    proxy_buffers               8 32k;
    proxy_busy_buffers_size     64k;
    proxy_temp_file_write_size  64k;
 
Also when using root path with nginx You might set the static files to false
in production.ini file::

  [app:main]
    use = egg:rhodecode
    full_stack = true
    static_files = false
    lang=en
    cache_dir = %(here)s/data

To not have the statics served by the application. And improve speed.

Apache reverse proxy
--------------------
Tutorial can be found here
http://wiki.pylonshq.com/display/pylonscookbook/Apache+as+a+reverse+proxy+for+Pylons


Apache's example FCGI config
----------------------------

TODO !

Other configuration files
-------------------------

Some extra configuration files and examples can be found here:
http://hg.python-works.com/rhodecode/files/tip/init.d

and also an celeryconfig file can be use from here:
http://hg.python-works.com/rhodecode/files/tip/celeryconfig.py

Troubleshooting
---------------

- missing static files ?

 - make sure either to set the `static_files = true` in the .ini file or
   double check the root path for Your http setup. It should point to 
   for example:
   /home/my-virtual-python/lib/python2.6/site-packages/rhodecode/public
   
- can't install celery/rabbitmq

 - don't worry RhodeCode works without them too. No extra setup required

- long lasting push timeouts ?

 - make sure You set a longer timeouts in Your proxy/fcgi settings, timeouts
   are caused by https server and not RhodeCode

- large pushes timeouts ?
 
 - make sure You set a proper max_body_size for the http server



.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _python: http://www.python.org/
.. _mercurial: http://mercurial.selenic.com/
.. _celery: http://celeryproject.org/
.. _rabbitmq: http://www.rabbitmq.com/