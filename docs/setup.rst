.. _setup:

Setup
=====


Setting up RhodeCode
--------------------

First, you will need to create a RhodeCode configuration file. Run the 
following command to do this::
 
    paster make-config RhodeCode production.ini

- This will create the file `production.ini` in the current directory. This
  configuration file contains the various settings for RhodeCode, e.g proxy 
  port, email settings, usage of static files, cache, celery settings and 
  logging.


Next, you need to create the databases used by RhodeCode. I recommend that you
use sqlite (default) or postgresql. If you choose a database other than the
default ensure you properly adjust the db url in your production.ini
configuration file to use this other database. Create the databases by running
the following command::

    paster setup-app production.ini

This will prompt you for a "root" path. This "root" path is the location where
RhodeCode will store all of its repositories on the current machine. After
entering this "root" path ``setup-app`` will also prompt you for a username 
and password for the initial admin account which ``setup-app`` sets up for you.

- The ``setup-app`` command will create all of the needed tables and an admin
  account. When choosing a root path you can either use a new empty location, 
  or a location which already contains existing repositories. If you choose a 
  location which contains existing repositories RhodeCode will simply add all 
  of the repositories at the chosen location to it's database. (Note: make 
  sure you specify the correct path to the root).
- Note: the given path for mercurial_ repositories **must** be write accessible
  for the application. It's very important since the RhodeCode web interface 
  will work without write access, but when trying to do a push it will 
  eventually fail with permission denied errors unless it has write access.

You are now ready to use RhodeCode, to run it simply execute::
 
    paster serve production.ini
 
- This command runs the RhodeCode server. The web app should be available at the 
  127.0.0.1:5000. This ip and port is configurable via the production.ini 
  file created in previous step
- Use the admin account you created above when running ``setup-app`` to login 
  to the web app.
- The default permissions on each repository is read, and the owner is admin. 
  Remember to update these if needed.
- In the admin panel you can toggle ldap, anonymous, permissions settings. As
  well as edit more advanced options on users and repositories

Try copying your own mercurial repository into the "root" directory you are
using, then from within the RhodeCode web application choose Admin >
repositories. Then choose Add New Repository. Add the repository you copied 
into the root. Test that you can browse your repository from within RhodeCode 
and then try cloning your repository from RhodeCode with::

    hg clone http://127.0.0.1:5000/<repository name>

where *repository name* is replaced by the name of your repository.

Using RhodeCode with SSH
------------------------

RhodeCode currently only hosts repositories using http and https. (The addition
of ssh hosting is a planned future feature.) However you can easily use ssh in
parallel with RhodeCode. (Repository access via ssh is a standard "out of
the box" feature of mercurial_ and you can use this to access any of the
repositories that RhodeCode is hosting. See PublishingRepositories_)

RhodeCode repository structures are kept in directories with the same name 
as the project. When using repository groups, each group is a subdirectory.
This allows you to easily use ssh for accessing repositories.

In order to use ssh you need to make sure that your web-server and the users 
login accounts have the correct permissions set on the appropriate directories.
(Note that these permissions are independent of any permissions you have set up
using the RhodeCode web interface.)

If your main directory (the same as set in RhodeCode settings) is for example
set to **/home/hg** and the repository you are using is named `rhodecode`, then
to clone via ssh you should run::

    hg clone ssh://user@server.com/home/hg/rhodecode

Using other external tools such as mercurial-server_ or using ssh key based
authentication is fully supported.

Note: In an advanced setup, in order for your ssh access to use the same
permissions as set up via the RhodeCode web interface, you can create an
authentication hook to connect to the rhodecode db and runs check functions for
permissions against that.
    
Setting up Whoosh full text search
----------------------------------

Starting from version 1.1 the whoosh index can be build by using the paster
command ``make-index``. To use ``make-index`` you must specify the configuration
file that stores the location of the index. You may specify the location of the 
repositories (`--repo-location`).  If not specified, this value is retrieved 
from the RhodeCode database.  This was required prior to 1.2.  Starting from 
version 1.2 it is also possible to specify a comma separated list of 
repositories (`--index-only`) to build index only on chooses repositories 
skipping any other found in repos location

You may optionally pass the option `-f` to enable a full index rebuild. Without
the `-f` option, indexing will run always in "incremental" mode.

For an incremental index build use::

	paster make-index production.ini 

For a full index rebuild use::

	paster make-index production.ini -f 


building index just for chosen repositories is possible with such command::
 
 paster make-index production.ini --index-only=vcs,rhodecode


In order to do periodical index builds and keep your index always up to date.
It's recommended to do a crontab entry for incremental indexing. 
An example entry might look like this::
 
    /path/to/python/bin/paster make-index /path/to/rhodecode/production.ini 
  
When using incremental mode (the default) whoosh will check the last
modification date of each file and add it to be reindexed if a newer file is
available. The indexing daemon checks for any removed files and removes them
from index.

If you want to rebuild index from scratch, you can use the `-f` flag as above,
or in the admin panel you can check `build from scratch` flag.


Setting up LDAP support
-----------------------

RhodeCode starting from version 1.1 supports ldap authentication. In order
to use LDAP, you have to install the python-ldap_ package. This package is 
available via pypi, so you can install it by running

using easy_install::

    easy_install python-ldap
 
using pip::

    pip install python-ldap

.. note::
   python-ldap requires some certain libs on your system, so before installing 
   it check that you have at least `openldap`, and `sasl` libraries.

LDAP settings are located in admin->ldap section,

Here's a typical ldap setup::

 Connection settings
 Enable LDAP          = checked
 Host                 = host.example.org
 Port                 = 389
 Account              = <account>
 Password             = <password>
 Connection Security  = LDAPS connection
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

Connection Security : required
    Defines the connection to LDAP server

    No encryption
        Plain non encrypted connection
        
    LDAPS connection
        Enable ldaps connection. It will likely require `Port`_ to be set to 
        a different value (standard LDAPS port is 636). When LDAPS is enabled 
        then `Certificate Checks`_ is required.
        
    START_TLS on LDAP connection
        START TLS connection

.. _Certificate Checks:

Certificate Checks : optional
    How SSL certificates verification is handled - this is only useful when
    `Enable LDAPS`_ is enabled.  Only DEMAND or HARD offer full SSL security 
    while the other options are susceptible to man-in-the-middle attacks.  SSL
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


Authentication by container or reverse-proxy
--------------------------------------------

Starting with version 1.3, RhodeCode supports delegating the authentication
of users to its WSGI container, or to a reverse-proxy server through which all
clients access the application.

When these authentication methods are enabled in RhodeCode, it uses the
username that the container/proxy (Apache/Nginx/etc) authenticated and doesn't
perform the authentication itself. The authorization, however, is still done by
RhodeCode according to its settings.

When a user logs in for the first time using these authentication methods,
a matching user account is created in RhodeCode with default permissions. An
administrator can then modify it using RhodeCode's admin interface.
It's also possible for an administrator to create accounts and configure their
permissions before the user logs in for the first time.

Container-based authentication
''''''''''''''''''''''''''''''

In a container-based authentication setup, RhodeCode reads the user name from
the ``REMOTE_USER`` server variable provided by the WSGI container.

After setting up your container (see `Apache's WSGI config`_), you'd need
to configure it to require authentication on the location configured for
RhodeCode.

In order for RhodeCode to start using the provided username, you should set the
following in the [app:main] section of your .ini file::

    container_auth_enabled = true


Proxy pass-through authentication
'''''''''''''''''''''''''''''''''

In a proxy pass-through authentication setup, RhodeCode reads the user name
from the ``X-Forwarded-User`` request header, which should be configured to be
sent by the reverse-proxy server.

After setting up your proxy solution (see `Apache virtual host reverse proxy example`_,
`Apache as subdirectory`_ or `Nginx virtual host example`_), you'd need to
configure the authentication and add the username in a request header named
``X-Forwarded-User``.

For example, the following config section for Apache sets a subdirectory in a
reverse-proxy setup with basic auth::

    <Location /<someprefix> >
      ProxyPass http://127.0.0.1:5000/<someprefix>
      ProxyPassReverse http://127.0.0.1:5000/<someprefix>
      SetEnvIf X-Url-Scheme https HTTPS=1

      AuthType Basic
      AuthName "RhodeCode authentication"
      AuthUserFile /home/web/rhodecode/.htpasswd
      require valid-user

      RequestHeader unset X-Forwarded-User

      RewriteEngine On
      RewriteCond %{LA-U:REMOTE_USER} (.+)
      RewriteRule .* - [E=RU:%1]
      RequestHeader set X-Forwarded-User %{RU}e
    </Location> 

In order for RhodeCode to start using the forwarded username, you should set
the following in the [app:main] section of your .ini file::

    proxypass_auth_enabled = true

.. note::
   If you enable proxy pass-through authentication, make sure your server is
   only accessible through the proxy. Otherwise, any client would be able to
   forge the authentication header and could effectively become authenticated
   using any account of their liking.

Integration with Issue trackers
-------------------------------

RhodeCode provides a simple integration with issue trackers. It's possible
to define a regular expression that will fetch issue id stored in commit
messages and replace that with an url to this issue. To enable this simply
uncomment following variables in the ini file::

    url_pat = (?:^#|\s#)(\w+)
    issue_server_link = https://myissueserver.com/{repo}/issue/{id}
    issue_prefix = #

`url_pat` is the regular expression that will fetch issues from commit messages.
Default regex will match issues in format of #<number> eg. #300.
 
Matched issues will be replace with the link specified as `issue_server_link` 
{id} will be replaced with issue id, and {repo} with repository name.
Since the # is striped `issue_prefix` is added as a prefix to url. 
`issue_prefix` can be something different than # if you pass 
ISSUE- as issue prefix this will generate an url in format::
 
  <a href="https://myissueserver.com/example_repo/issue/300">ISSUE-300</a>  

Hook management
---------------

Hooks can be managed in similar way to this used in .hgrc files.
To access hooks setting click `advanced setup` on Hooks section of Mercurial
Settings in Admin. 

There are 4 built in hooks that cannot be changed (only enable/disable by
checkboxes on previos section).
To add another custom hook simply fill in first section with 
<name>.<hook_type> and the second one with hook path. Example hooks
can be found at *rhodecode.lib.hooks*. 


Changing default encoding
-------------------------

By default RhodeCode uses utf8 encoding, starting from 1.3 series this
can be changed, simply edit default_encoding in .ini file to desired one.
This affects many parts in rhodecode including commiters names, filenames,
encoding of commit messages. In addition RhodeCode can detect if `chardet`
library is installed. If `chardet` is detected RhodeCode will fallback to it
when there are encode/decode errors.


Setting Up Celery
-----------------

Since version 1.1 celery is configured by the rhodecode ini configuration files.
Simply set use_celery=true in the ini file then add / change the configuration 
variables inside the ini file.

Remember that the ini files use the format with '.' not with '_' like celery.
So for example setting `BROKER_HOST` in celery means setting `broker.host` in
the config file.

In order to start using celery run::

 paster celeryd <configfile.ini>


.. note::
   Make sure you run this command from the same virtualenv, and with the same 
   user that rhodecode runs.
   
HTTPS support
-------------

There are two ways to enable https:

- Set HTTP_X_URL_SCHEME in your http server headers, than rhodecode will
  recognize this headers and make proper https redirections
- Alternatively, change the `force_https = true` flag in the ini configuration 
  to force using https, no headers are needed than to enable https


Nginx virtual host example
--------------------------

Sample config for nginx using proxy::

    upstream rc {
        server 127.0.0.1:5000;
        # add more instances for load balancing
        #server 127.0.0.1:5001;
        #server 127.0.0.1:5002;
    }
    
    server {
       listen          80;
       server_name     hg.myserver.com;
       access_log      /var/log/nginx/rhodecode.access.log;
       error_log       /var/log/nginx/rhodecode.error.log;

       location / {
            try_files $uri @rhode;
       }
    
       location @rhode {
            proxy_pass      http://rc;
            include         /etc/nginx/proxy.conf;
       }

    }  
  
Here's the proxy.conf. It's tuned so it will not timeout on long
pushes or large pushes::
    
    proxy_redirect              off;
    proxy_set_header            Host $host;
    proxy_set_header            X-Url-Scheme $scheme;
    proxy_set_header            X-Host $http_host;
    proxy_set_header            X-Real-IP $remote_addr;
    proxy_set_header            X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header            Proxy-host $proxy_host;
    client_max_body_size        400m;
    client_body_buffer_size     128k;
    proxy_buffering             off;
    proxy_connect_timeout       7200;
    proxy_send_timeout          7200;
    proxy_read_timeout          7200;
    proxy_buffers               8 32k;
 
Also, when using root path with nginx you might set the static files to false
in the production.ini file::

    [app:main]
      use = egg:rhodecode
      full_stack = true
      static_files = false
      lang=en
      cache_dir = %(here)s/data

In order to not have the statics served by the application. This improves speed.


Apache virtual host reverse proxy example
-----------------------------------------

Here is a sample configuration file for apache using proxy::

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

    <Location /<someprefix> >
      ProxyPass http://127.0.0.1:5000/<someprefix>
      ProxyPassReverse http://127.0.0.1:5000/<someprefix>
      SetEnvIf X-Url-Scheme https HTTPS=1
    </Location> 

Besides the regular apache setup you will need to add the following line
into [app:main] section of your .ini file::

    filter-with = proxy-prefix

Add the following at the end of the .ini file::

    [filter:proxy-prefix]
    use = egg:PasteDeploy#prefix
    prefix = /<someprefix> 


then change <someprefix> into your choosen prefix

Apache's WSGI config
--------------------

Alternatively, RhodeCode can be set up with Apache under mod_wsgi. For
that, you'll need to:

- Install mod_wsgi. If using a Debian-based distro, you can install
  the package libapache2-mod-wsgi::

    aptitude install libapache2-mod-wsgi

- Enable mod_wsgi::

    a2enmod wsgi

- Create a wsgi dispatch script, like the one below. Make sure you
  check the paths correctly point to where you installed RhodeCode
  and its Python Virtual Environment.
- Enable the WSGIScriptAlias directive for the wsgi dispatch script,
  as in the following example. Once again, check the paths are
  correctly specified.

Here is a sample excerpt from an Apache Virtual Host configuration file::

    WSGIDaemonProcess pylons user=www-data group=www-data processes=1 \
        threads=4 \
        python-path=/home/web/rhodecode/pyenv/lib/python2.6/site-packages
    WSGIScriptAlias / /home/web/rhodecode/dispatch.wsgi

Example wsgi dispatch script::

    import os
    os.environ["HGENCODING"] = "UTF-8"
    os.environ['PYTHON_EGG_CACHE'] = '/home/web/rhodecode/.egg-cache'
    
    # sometimes it's needed to set the curent dir
    os.chdir('/home/web/rhodecode/') 

    import site
    site.addsitedir("/home/web/rhodecode/pyenv/lib/python2.6/site-packages")
    
    from paste.deploy import loadapp
    from paste.script.util.logging_config import fileConfig

    fileConfig('/home/web/rhodecode/production.ini')
    application = loadapp('config:/home/web/rhodecode/production.ini')

Note: when using mod_wsgi you'll need to install the same version of
Mercurial that's inside RhodeCode's virtualenv also on the system's Python
environment.


Other configuration files
-------------------------

Some example init.d scripts can be found here, for debian and gentoo:

https://rhodecode.org/rhodecode/files/tip/init.d


Troubleshooting
---------------

:Q: **Missing static files?**
:A: Make sure either to set the `static_files = true` in the .ini file or
   double check the root path for your http setup. It should point to 
   for example:
   /home/my-virtual-python/lib/python2.6/site-packages/rhodecode/public
   
| 

:Q: **Can't install celery/rabbitmq**
:A: Don't worry RhodeCode works without them too. No extra setup is required.

|
 
:Q: **Long lasting push timeouts?**
:A: Make sure you set a longer timeouts in your proxy/fcgi settings, timeouts
    are caused by https server and not RhodeCode.
    
| 

:Q: **Large pushes timeouts?**
:A: Make sure you set a proper max_body_size for the http server.

|

:Q: **Apache doesn't pass basicAuth on pull/push?**
:A: Make sure you added `WSGIPassAuthorization true`.

For further questions search the `Issues tracker`_, or post a message in the 
`google group rhodecode`_

.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _python: http://www.python.org/
.. _mercurial: http://mercurial.selenic.com/
.. _celery: http://celeryproject.org/
.. _rabbitmq: http://www.rabbitmq.com/
.. _python-ldap: http://www.python-ldap.org/
.. _mercurial-server: http://www.lshift.net/mercurial-server.html
.. _PublishingRepositories: http://mercurial.selenic.com/wiki/PublishingRepositories
.. _Issues tracker: https://bitbucket.org/marcinkuzminski/rhodecode/issues
.. _google group rhodecode: http://groups.google.com/group/rhodecode
