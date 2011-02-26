.. _setup:

Setup
=====


Setting up RhodeCode
--------------------------

First, you will need to create a RhodeCode configuration file. Run the following
command to do this::
 
 paster make-config RhodeCode production.ini

- This will create the file `production.ini` in the current directory. This
  configuration file contains the various settings for RhodeCode, e.g proxy port,
  email settings, usage of static files, cache, celery settings and logging.


Next, you need to create the databases used by RhodeCode. I recommend that you
use sqlite (default) or postgresql. If you choose a database other than the
default ensure you properly adjust the db url in your production.ini
configuration file to use this other database. Create the databases by running
the following command::

 paster setup-app production.ini

This will prompt you for a "root" path. This "root" path is the location where
RhodeCode will store all of its repositories on the current machine. After
entering this "root" path ``setup-app`` will also prompt you for a username and password
for the initial admin account which ``setup-app`` sets up for you.

- The ``setup-app`` command will create all of the needed tables and an admin
  account. When choosing a root path You can either use a new empty location, or a
  location which already contains existing repositories. If you choose a location
  which contains existing repositories RhodeCode will simply add all of the
  repositories at the chosen location to it's database. (Note: make sure you
  specify the correct path to the root).
- Note: the given path for mercurial_ repositories **must** be write accessible
  for the application. It's very important since the RhodeCode web interface will
  work without write access, but when trying to do a push it will eventually fail
  with permission denied errors unless it has write access.

You are now ready to use RhodeCode, to run it simply execute::
 
 paster serve production.ini
 
- This command runs the RhodeCode server. The web app should be available at the 
  127.0.0.1:5000. This ip and port is configurable via the production.ini 
  file created in previous step
- Use the admin account you created above when running ``setup-app`` to login to the web app.
- The default permissions on each repository is read, and the owner is admin. 
  Remember to update these if needed.
- In the admin panel You can toggle ldap, anonymous, permissions settings. As
  well as edit more advanced options on users and repositories

Try copying your own mercurial repository into the "root" directory you are
using, then from within the RhodeCode web application choose Admin >
repositories. Then choose Add New Repository. Add the repository you copied into
the root. Test that you can browse your repository from within RhodCode and then
try cloning your repository from RhodeCode with::

  hg clone http://127.0.0.1:5000/<repository name>

where *repository name* is replaced by the name of your repository.

Using RhodeCode with SSH
------------------------

RhodeCode repository structures are kept in directories with the same name 
as the project, when using repository groups, each group is a subdirectory.
This will allow you to use ssh for accessing repositories quite easily. There
are some exceptions when using ssh for accessing repositories.

You have to make sure that the web-server as well as the ssh users have unix
permission for the appropriate directories. Secondly, when using ssh rhodecode
will not authenticate those requests and permissions set by the web interface
will not work on the repositories accessed via ssh. There is a solution to this
to use auth hooks, that connects to rhodecode db, and runs check functions for
permissions.


If your main directory (the same as set in RhodeCode settings) is for example
set to **/home/hg** and the repository you are using is named `rhodecode`, then
to clone via ssh you should run::

    hg clone ssh://user@server.com/home/hg/rhodecode
  
Using external tools such as mercurial server or using ssh key based
authentication is fully supported.
    
Setting up Whoosh full text search
----------------------------------

Starting from version 1.1 the whoosh index can be build by using the paster
command ``make-index``. To use ``make-index`` You must specify the configuration
file that stores the location of the index, and the location of the repositories
(`--repo-location`).

You may optionally pass the option `-f` to enable a full index rebuild. Without
the `-f` option, indexing will run always in "incremental" mode.

For an incremental index build use::

	paster make-index production.ini --repo-location=<location for repos> 


For a full index rebuild use::

	paster make-index production.ini -f --repo-location=<location for repos>

- For full text search you can either put crontab entry for

In order to do periodical index builds and keep your index always up to date.
It's recommended to do a crontab entry for incremental indexing. 
An example entry might look like this::
 
 /path/to/python/bin/paster /path/to/rhodecode/production.ini --repo-location=<location for repos> 
  
When using incremental mode (the default) whoosh will check the last
modification date of each file and add it to be reindexed if a newer file is
available. The indexing daemon checks for any removed files and removes them
from index.

If you want to rebuild index from scratch, you can use the `-f` flag as above,
or in the admin panel you can check `build from scratch` flag.


Setting up LDAP support
-----------------------

RhodeCode starting from version 1.1 supports ldap authentication. In order
to use LDAP, you have to install python-ldap_ package. This package is available
via pypi, so you can install it by running

::

 easy_install python-ldap
 
::

 pip install python-ldap

.. note::
   python-ldap requires some certain libs on your system, so before installing 
   it check that you have at least `openldap`, and `sasl` libraries.

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
authentication so those are credentials to access your ldap, if it doesn't 
support anonymous search/user lookups. 

Base DN must have %(user)s template inside, it's a placer where your uid used
to login would go, it allows admins to specify not standard schema for uid 
variable

If all data are entered correctly, and `python-ldap` is properly installed
Users should be granted to access RhodeCode wit ldap accounts. When 
logging at the first time an special ldap account is created inside RhodeCode, 
so you can control over permissions even on ldap users. If such user exists 
already in RhodeCode database ldap user with the same username would be not 
able to access RhodeCode.

If you have problems with ldap access and believe you entered correct 
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
   Make sure you run this command from same virtualenv, and with the same user
   that rhodecode runs.
   
HTTPS support
-------------

There are two ways to enable https, first is to set HTTP_X_URL_SCHEME in
your http server headers, than rhodecode will recognise this headers and make
proper https redirections, another way is to set `force_https = true` 
in the ini cofiguration to force using https, no headers are needed than to
enable https


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
               #this is important if you want to use https !!!
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
    proxy_buffer_size           16k;
    proxy_buffers               4 16k;
    proxy_busy_buffers_size     64k;
    proxy_temp_file_write_size  64k;
 
Also when using root path with nginx you might set the static files to false
in production.ini file::

    [app:main]
      use = egg:rhodecode
      full_stack = true
      static_files = false
      lang=en
      cache_dir = %(here)s/data

To not have the statics served by the application. And improve speed.


Apache virtual host example
---------------------------

Sample config for apache using proxy::

    <VirtualHost *:80>
            ServerName hg.myserver.com
            ServerAlias hg.myserver.com
    
            <Proxy *>
              Order allow,deny
              Allow from all
            </Proxy>
    
            #important !
            #Directive to properly generate url (clone url) for pylons
            ProxyPreserveHost On
    
            #rhodecode instance
            ProxyPass / http://127.0.0.1:5000/
            ProxyPassReverse / http://127.0.0.1:5000/
            
            #to enable https use line below
            #SetEnvIf X-Url-Scheme https HTTPS=1
            
    </VirtualHost> 


Additional tutorial
http://wiki.pylonshq.com/display/pylonscookbook/Apache+as+a+reverse+proxy+for+Pylons


Apache as subdirectory
----------------------


Apache subdirectory part::

    <Location /rhodecode>
      ProxyPass http://127.0.0.1:59542/rhodecode
      ProxyPassReverse http://127.0.0.1:59542/rhodecode
      SetEnvIf X-Url-Scheme https HTTPS=1
    </Location> 

Besides the regular apache setup you will need to add such part to .ini file::

    filter-with = proxy-prefix

Add the following at the end of the .ini file::

    [filter:proxy-prefix]
    use = egg:PasteDeploy#prefix
    prefix = /<someprefix> 


Apache's example FCGI config
----------------------------

TODO !

Other configuration files
-------------------------

Some example init.d script can be found here, for debian and gentoo:

https://rhodeocode.org/rhodecode/files/tip/init.d


Troubleshooting
---------------

- missing static files ?

 - make sure either to set the `static_files = true` in the .ini file or
   double check the root path for your http setup. It should point to 
   for example:
   /home/my-virtual-python/lib/python2.6/site-packages/rhodecode/public
   
- can't install celery/rabbitmq

 - don't worry RhodeCode works without them too. No extra setup required

- long lasting push timeouts ?

 - make sure you set a longer timeouts in your proxy/fcgi settings, timeouts
   are caused by https server and not RhodeCode

- large pushes timeouts ?
 
 - make sure you set a proper max_body_size for the http server

- Apache doesn't pass basicAuth on pull/push ?

 - Make sure you added `WSGIPassAuthorization true` 

.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _python: http://www.python.org/
.. _mercurial: http://mercurial.selenic.com/
.. _celery: http://celeryproject.org/
.. _rabbitmq: http://www.rabbitmq.com/
.. _python-ldap: http://www.python-ldap.org/
