.. _setup:

Setup
=====


Setting up the application
--------------------------

First You'll need to create RhodeCode config file. Run the following command 
to do this

::
 
 paster make-config RhodeCode production.ini

- This will create `production.ini` config inside the directory
  this config contains various settings for RhodeCode, e.g proxy port, 
  email settings, usage of static files, cache, celery settings and logging.


Next we need to create the database. I'll recommend to use sqlite (default) 
or postgresql. Make sure You properly adjust the db url in the .ini file to use
other than the default sqlite database


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

You are ready to use RhodeCode, to run it simply execute

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
  
Using RhodeCode with SSH
------------------------

RhodeCode repository structures are kept in directories with the same name 
as the project, when using repository groups, each group is a a subdirectory.
This will allow You to use ssh for accessing repositories quite easy. There
are some exceptions when using ssh for accessing repositories.

You have to make sure that the webserver as well as the ssh users have unix
permission for directories. Secondly when using ssh rhodecode will not 
authenticate those requests and permissions set by the web interface will not
work on the repositories accessed via ssh. There is a solution to this to use 
auth hooks, that connects to rhodecode db, and runs check functions for
permissions.

TODO: post more info on this !

if Your main directory (the same as set in RhodeCode settings) is set to
for example `\home\hg` and repository You are using is `rhodecode`

The command runned should look like this::
 hg clone ssh://user@server.com/home/hg/rhodecode
 
Using external tools such as mercurial server or using ssh key based auth is
fully supported.
    
Setting up Whoosh full text search
----------------------------------

Starting from version 1.1 whoosh index can be build using paster command.
You have to specify the config file that stores location of index, and
location of repositories (`--repo-location`). Starting from version 1.2 it is 
also possible to specify a comma separated list of repositories (`--index-only`)
to build index only on chooses repositories skipping any other found in repos
location

There is possible also to pass `-f` to the options
to enable full index rebuild. Without that indexing will run always in in
incremental mode.

incremental mode::

	paster make-index production.ini --repo-location=<location for repos> 



for full index rebuild You can use::

	paster make-index production.ini -f --repo-location=<location for repos>


building index just for chosen repositories is possible with such command::
 
 paster make-index production.ini --repo-location=<location for repos> --index-only=vcs,rhodecode


In order to do periodical index builds and keep Your index always up to date.
It's recommended to do a crontab entry for incremental indexing. 
An example entry might look like this

::
 
 /path/to/python/bin/paster /path/to/rhodecode/production.ini --repo-location=<location for repos> 
  
When using incremental (default) mode whoosh will check last modification date 
of each file and add it to reindex if newer file is available. Also indexing 
daemon checks for removed files and removes them from index. 

Sometime You might want to rebuild index from scratch. You can do that using 
the `-f` flag passed to paster command or, in admin panel You can check 
`build from scratch` flag.


Setting up LDAP support
-----------------------

RhodeCode starting from version 1.1 supports ldap authentication. In order
to use LDAP, You have to install python-ldap_ package. This package is available
via pypi, so You can install it by running

::

 easy_install python-ldap
 
::

 pip install python-ldap

.. note::
   python-ldap requires some certain libs on Your system, so before installing 
   it check that You have at least `openldap`, and `sasl` libraries.

LDAP settings are located in admin->ldap section,

This is a typical LDAP setup::

 Connection settings
 Enable LDAP          = checked
 Host                 = host.example.org
 Port                 = 389
 Account              = <account>
 Password             = <password>
 Enable LDAPS         = checked
 Certificate Checks   = DEMAND

 Search settings
 Base DN              = CN=users,DC=host,DC=example,DC=org
 LDAP Filter          = (&(objectClass=user)(!(objectClass=computer)))
 LDAP Search Scope    = SUBTREE

 Attribute mappings
 Login Attribute      = uid
 First Name Attribute = firstName
 Last Name Attribute  = lastName
 E-mail Attribute     = mail

.. _enable_ldap:

Enable LDAP : required
    Whether to use LDAP for authenticating users.

.. _ldap_host:

Host : required
    LDAP server hostname or IP address.

.. _Port:

Port : required
    389 for un-encrypted LDAP, 636 for SSL-encrypted LDAP.

.. _ldap_account:

Account : optional
    Only required if the LDAP server does not allow anonymous browsing of
    records.  This should be a special account for record browsing.  This
    will require `LDAP Password`_ below.

.. _LDAP Password:

Password : optional
    Only required if the LDAP server does not allow anonymous browsing of
    records.

.. _Enable LDAPS:

Enable LDAPS : optional
    Check this if SSL encryption is necessary for communication with the
    LDAP server - it will likely require `Port`_ to be set to a different
    value (standard LDAPS port is 636).  When LDAPS is enabled then
    `Certificate Checks`_ is required.

.. _Certificate Checks:

Certificate Checks : optional
    How SSL certificates verification is handled - this is only useful when
    `Enable LDAPS`_ is enabled.  Only DEMAND or HARD offer full SSL security while
    the other options are susceptible to man-in-the-middle attacks.  SSL
    certificates can be installed to /etc/openldap/cacerts so that the
    DEMAND or HARD options can be used with self-signed certificates or
    certificates that do not have traceable certificates of authority.

    NEVER
        A serve certificate will never be requested or checked.

    ALLOW
        A server certificate is requested.  Failure to provide a
        certificate or providing a bad certificate will not terminate the
        session.

    TRY
        A server certificate is requested.  Failure to provide a
        certificate does not halt the session; providing a bad certificate
        halts the session.

    DEMAND
        A server certificate is requested and must be provided and
        authenticated for the session to proceed.

    HARD
        The same as DEMAND.

.. _Base DN:

Base DN : required
    The Distinguished Name (DN) where searches for users will be performed.
    Searches can be controlled by `LDAP Filter`_ and `LDAP Search Scope`_.

.. _LDAP Filter:

LDAP Filter : optional
    A LDAP filter defined by RFC 2254.  This is more useful when `LDAP
    Search Scope`_ is set to SUBTREE.  The filter is useful for limiting
    which LDAP objects are identified as representing Users for
    authentication.  The filter is augmented by `Login Attribute`_ below.
    This can commonly be left blank.

.. _LDAP Search Scope:

LDAP Search Scope : required
    This limits how far LDAP will search for a matching object.

    BASE
        Only allows searching of `Base DN`_ and is usually not what you
        want.

    ONELEVEL
        Searches all entries under `Base DN`_, but not Base DN itself.

    SUBTREE
        Searches all entries below `Base DN`_, but not Base DN itself.
        When using SUBTREE `LDAP Filter`_ is useful to limit object
        location.

.. _Login Attribute:

Login Attribute : required        
    The LDAP record attribute that will be matched as the USERNAME or
    ACCOUNT used to connect to RhodeCode.  This will be added to `LDAP
    Filter`_ for locating the User object.  If `LDAP Filter`_ is specified as
    "LDAPFILTER", `Login Attribute`_ is specified as "uid" and the user has
    connected as "jsmith" then the `LDAP Filter`_ will be augmented as below
    ::

        (&(LDAPFILTER)(uid=jsmith))

.. _ldap_attr_firstname:

First Name Attribute : required
    The LDAP record attribute which represents the user's first name.

.. _ldap_attr_lastname:

Last Name Attribute : required
    The LDAP record attribute which represents the user's last name.

.. _ldap_attr_email:

Email Attribute : required
    The LDAP record attribute which represents the user's email address.

If all data are entered correctly, and python-ldap_ is properly installed
users should be granted access to RhodeCode with ldap accounts.  At this
time user information is copied from LDAP into the RhodeCode user database.
This means that updates of an LDAP user object may not be reflected as a
user update in RhodeCode.

If You have problems with LDAP access and believe You entered correct
information check out the RhodeCode logs, any error messages sent from LDAP
will be saved there.

Active Directory
''''''''''''''''

RhodeCode can use Microsoft Active Directory for user authentication.  This
is done through an LDAP or LDAPS connection to Active Directory.  The
following LDAP configuration settings are typical for using Active
Directory ::

 Base DN              = OU=SBSUsers,OU=Users,OU=MyBusiness,DC=v3sys,DC=local
 Login Attribute      = sAMAccountName
 First Name Attribute = givenName
 Last Name Attribute  = sn
 E-mail Attribute     = mail

All other LDAP settings will likely be site-specific and should be
appropriately configured.

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
   
HTTPS support
-------------

There are two ways to enable https, first is to set HTTP_X_URL_SCHEME in
Your http server headers, than rhodecode will recognise this headers and make
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
            #this is important if You want to use https !!!
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
 
Also when using root path with nginx You might set the static files to false
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

Besides the regular apache setup You'll need to add such part to .ini file::

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

- Apache doesn't pass basicAuth on pull/push ?

 - Make sure You added `WSGIPassAuthorization true` 

.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _python: http://www.python.org/
.. _mercurial: http://mercurial.selenic.com/
.. _celery: http://celeryproject.org/
.. _rabbitmq: http://www.rabbitmq.com/
.. _python-ldap: http://www.python-ldap.org/
