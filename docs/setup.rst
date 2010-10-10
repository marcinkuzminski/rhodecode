.. _setup:

Setup
=====


Setting up the application
--------------------------

::
 
 paster make-config RhodeCode production.ini

- This will create `production.ini` config inside the directory
  this config contain various settings for rhodecode, e.g port, email settings
  static files, cache and logging.

::

 paster setup-app production.ini` 

- This command will create all needed tables and an admin account. 
  When asked for a path You can either use a new location of one with already 
  existing ones. RhodeCode will simply add all new found repositories to 
  it's database. Also make sure You specify correct path to repositories.
- Remember that the given path for mercurial_ repositories must be write 
  accessible for the application. It's very important since RhodeCode web interface
  will work even without such an access but, when trying to do a push it'll 
  eventually faile with permission denied errors. 
- Run 

::
 
 paster serve production.ini
 
- This command runs the rhodecode server the app should be available at the 
  127.0.0.1:5000. This ip and port is configurable via the production.ini 
  file  created in previos step
- Use admin account you created to login.
- Default permissions on each repository is read, and owner is admin. So 
  remember to update these.

- All needed configs are inside rhodecode sources ie. celeryconfig.py, 
  development.ini, production.ini You can configure the email, ports, loggers, 
  workers from there.
  
Setting up Whoosh
-----------------

- For full text search You can either put crontab entry for

::
 
 python /var/www/rhodecode/rhodecode/lib/indexers/daemon.py incremental <put_here_path_to_repos>
  
When using incremental mode whoosh will check last modification date of each file
and add it to reindex if newer file is available. Also indexing daemon checks
for removed files and removes them from index. Sometime You might want to rebuild
index from scrach, in admin pannel You can check `build from scratch` flag
and in standalone daemon You can pass `full` instead on incremental to build
remove previos index and build new one.

Nginx virtual host example
--------------------------

Sample config for nginx::

 server {
    listen          80;
    server_name     hg.myserver.com;
    access_log      /var/log/nginx/rhodecode.access.log;
    error_log      /var/log/nginx/rhodecode.error.log;
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
  
Here's the proxy.conf. It's tunned so it'll not timeout on long
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

To not have the statics served by the application.


.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _python: http://www.python.org/
.. _mercurial: http://mercurial.selenic.com/
.. _celery: http://celeryproject.org/
.. _rabbitmq: http://www.rabbitmq.com/