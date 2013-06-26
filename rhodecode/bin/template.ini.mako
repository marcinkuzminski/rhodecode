## -*- coding: utf-8 -*-
<%text>
################################################################################
################################################################################
# RhodeCode - Example config                                                   #
# Built-in functions and variables                                             #
# The ${here} variable will be replaced with the parent directory of this file #
# ${uuid()} function will generate a unique hash                               #
################################################################################
</%text>
[DEFAULT]
debug = true
pdebug = false
<%text>
################################################################################
## Uncomment and replace with the address which should receive                ## 
## any error reports after application crash                                  ##
## Additionally those settings will be used by RhodeCode mailing system       ##
################################################################################
</%text>
#email_to = admin@localhost
#error_email_from = paste_error@localhost
#app_email_from = rhodecode-noreply@localhost
#error_message =
#email_prefix = [RhodeCode]

#smtp_server = mail.server.com
#smtp_username = 
#smtp_password = 
#smtp_port = 
#smtp_use_tls = false
#smtp_use_ssl = true
<%text>## Specify available auth parameters here (e.g. LOGIN PLAIN CRAM-MD5, etc.)</%text>
#smtp_auth = 

[server:main]
%if http_server == 'paste':
<%text>## PASTE ##</%text>
use = egg:Paste#http
<%text>## nr of worker threads to spawn</%text>
threadpool_workers = 5
<%text>## max request before thread respawn</%text>
threadpool_max_requests = 10
<%text>## option to use threads of process</%text>
use_threadpool = true
%endif
%if http_server == 'waitress':
<%text>## WAITRESS ##</%text>
use = egg:waitress#main
<%text>## number of worker threads</%text>
threads = 5
<%text>## MAX BODY SIZE 100GB</%text>
max_request_body_size = 107374182400
<%text>## use poll instead of select, fixes fd limits, may not work on old</%text>
<%text>## windows systems.</%text>
#asyncore_use_poll = True
%endif
%if http_server == 'gunicorn':
<%text>## GUNICORN ##</%text>
use = egg:gunicorn#main
<%text>## number of process workers. You must set `instance_id = *` when this option</%text>
<%text>## is set to more than one worker</%text>
workers = 1
<%text>## process name</%text>
proc_name = rhodecode
<%text>## type of worker class, one of sync, eventlet, gevent, tornado</%text>
<%text>## recommended for bigger setup is using of of other than sync one</%text>
worker_class = sync
max_requests = 1000
<%text>## ammount of time a worker can handle request before it get's killed and</%text>
<%text>## restarted</%text>
timeout = 3600
%endif
<%text>## COMMON ##</%text>
host = ${host}
port = ${port}

<%text>## prefix middleware for rc</%text>
#[filter:proxy-prefix]
#use = egg:PasteDeploy#prefix
#prefix = /<your-prefix>

[app:main]
use = egg:rhodecode
<%text>## enable proxy prefix middleware</%text>
#filter-with = proxy-prefix

full_stack = true
static_files = true
<%text>## Optional Languages</%text>
<%text>## en, fr, ja, pt_BR, zh_CN, zh_TW, pl, ru</%text>
lang = ${lang}
cache_dir = ${here}/data
index_dir = ${here}/data/index

<%text>## perform a full repository scan on each server start, this should be</%text>
<%text>## set to false after first startup, to allow faster server restarts.</%text>
initial_repo_scan = false

<%text>## uncomment and set this path to use archive download cache</%text>
archive_cache_dir = ${here}/tarballcache

<%text>## change this to unique ID for security</%text>
app_instance_uuid = ${uuid()}

<%text>## cut off limit for large diffs (size in bytes)</%text>
cut_off_limit = 256000

<%text>## use cache version of scm repo everywhere</%text>
vcs_full_cache = true

<%text>## force https in RhodeCode, fixes https redirects, assumes it's always https</%text>
force_https = false

<%text>## use Strict-Transport-Security headers</%text>
use_htsts = false

<%text>## number of commits stats will parse on each iteration</%text>
commit_parse_limit = 25

<%text>## use gravatar service to display avatars</%text>
use_gravatar = true

<%text>## path to git executable</%text>
git_path = git

<%text>## git rev filter option, --all is the default filter, if you need to</%text>
<%text>## hide all refs in changelog switch this to --branches --tags</%text>
git_rev_filter=--branches --tags

<%text>## RSS feed options</%text>
rss_cut_off_limit = 256000
rss_items_per_page = 10
rss_include_diff = false

<%text>## options for showing and identifying changesets</%text>
show_sha_length = 12
show_revision_number = true

<%text>## gist URL alias, used to create nicer urls for gist. This should be an</%text>
<%text>## url that does rewrites to _admin/gists/<gistid>.</%text>
<%text>## example: http://gist.rhodecode.org/{gistid}. Empty means use the internal</%text>
<%text>## RhodeCode url, ie. http[s]://rhodecode.server/_admin/gists/<gistid></%text>
gist_alias_url =

<%text>## white list of API enabled controllers. This allows to add list of</%text>
<%text>## controllers to which access will be enabled by api_key. eg: to enable</%text>
<%text>## api access to raw_files put `FilesController:raw`, to enable access to patches</%text>
<%text>## add `ChangesetController:changeset_patch`. This list should be "," separated</%text>
<%text>## Syntax is <ControllerClass>:<function>. Check debug logs for generated names</%text>
api_access_controllers_whitelist =

<%text>## alternative_gravatar_url allows you to use your own avatar server application</%text>
<%text>## the following parts of the URL will be replaced</%text>
<%text>## {email}        user email</%text>
<%text>## {md5email}     md5 hash of the user email (like at gravatar.com)</%text>
<%text>## {size}         size of the image that is expected from the server application</%text>
<%text>## {scheme}       http/https from RhodeCode server</%text>
<%text>## {netloc}       network location from RhodeCode server</%text>
#alternative_gravatar_url = http://myavatarserver.com/getbyemail/{email}/{size}
#alternative_gravatar_url = http://myavatarserver.com/getbymd5/{md5email}?s={size}


<%text>## container auth options</%text>
container_auth_enabled = false
proxypass_auth_enabled = false

<%text>## default encoding used to convert from and to unicode</%text>
<%text>## can be also a comma seperated list of encoding in case of mixed encodings</%text>
default_encoding = utf8

<%text>## overwrite schema of clone url</%text>
<%text>## available vars:</%text>
<%text>## scheme - http/https</%text>
<%text>## user - current user</%text>
<%text>## pass - password</%text>
<%text>## netloc - network location</%text>
<%text>## path - usually repo_name</%text>

#clone_uri = {scheme}://{user}{pass}{netloc}{path}

<%text>## issue tracker for RhodeCode (leave blank to disable, absent for default)</%text>
#bugtracker = http://bitbucket.org/marcinkuzminski/rhodecode/issues

<%text>## issue tracking mapping for commits messages</%text>
<%text>## comment out issue_pat, issue_server, issue_prefix to enable</%text>

<%text>## pattern to get the issues from commit messages</%text>
<%text>## default one used here is #<numbers> with a regex passive group for `#`</%text>
<%text>## {id} will be all groups matched from this pattern</%text>

issue_pat = (?:\s*#)(\d+)

<%text>## server url to the issue, each {id} will be replaced with match</%text>
<%text>## fetched from the regex and {repo} is replaced with full repository name</%text>
<%text>## including groups {repo_name} is replaced with just name of repo</%text>

issue_server_link = https://myissueserver.com/{repo}/issue/{id}

<%text>## prefix to add to link to indicate it's an url</%text>
<%text>## #314 will be replaced by <issue_prefix><id></%text>

issue_prefix = #

<%text>## issue_pat, issue_server_link, issue_prefix can have suffixes to specify</%text>
<%text>## multiple patterns, to other issues server, wiki or others</%text>
<%text>## below an example how to create a wiki pattern</%text>
<%text>## wiki-some-id -> https://mywiki.com/some-id</%text>

#issue_pat_wiki = (?:wiki-)(.+)
#issue_server_link_wiki = https://mywiki.com/{id}
#issue_prefix_wiki = WIKI-


<%text>## instance-id prefix</%text>
<%text>## a prefix key for this instance used for cache invalidation when running</%text>
<%text>## multiple instances of rhodecode, make sure it's globally unique for</%text>
<%text>## all running rhodecode instances. Leave empty if you don't use it</%text>
instance_id = 

<%text>## alternative return HTTP header for failed authentication. Default HTTP</%text>
<%text>## response is 401 HTTPUnauthorized. Currently HG clients have troubles with</%text>
<%text>## handling that. Set this variable to 403 to return HTTPForbidden</%text>
auth_ret_code =

<%text>## locking return code. When repository is locked return this HTTP code. 2XX</%text>
<%text>## codes don't break the transactions while 4XX codes do</%text>
lock_ret_code = 423

<%text>## allows to change the repository location in settings page</%text>
allow_repo_location_change = True

<%text>## allows to setup custom hooks in settings page</%text>
allow_custom_hooks_settings = True

<%text>
####################################
###        CELERY CONFIG        ####
####################################
</%text>
use_celery = false
broker.host = localhost
broker.vhost = rabbitmqhost
broker.port = 5672
broker.user = rabbitmq
broker.password = qweqwe

celery.imports = rhodecode.lib.celerylib.tasks

celery.result.backend = amqp
celery.result.dburi = amqp://
celery.result.serialier = json

#celery.send.task.error.emails = true
#celery.amqp.task.result.expires = 18000

celeryd.concurrency = 2
#celeryd.log.file = celeryd.log
celeryd.log.level = debug
celeryd.max.tasks.per.child = 1

<%text>## tasks will never be sent to the queue, but executed locally instead.</%text>
celery.always.eager = false
<%text>
####################################
###         BEAKER CACHE        ####
####################################
</%text>
beaker.cache.data_dir=${here}/data/cache/data
beaker.cache.lock_dir=${here}/data/cache/lock

beaker.cache.regions=super_short_term,short_term,long_term,sql_cache_short,sql_cache_med,sql_cache_long

beaker.cache.super_short_term.type=memory
beaker.cache.super_short_term.expire=10
beaker.cache.super_short_term.key_length = 256

beaker.cache.short_term.type=memory
beaker.cache.short_term.expire=60
beaker.cache.short_term.key_length = 256

beaker.cache.long_term.type=memory
beaker.cache.long_term.expire=36000
beaker.cache.long_term.key_length = 256

beaker.cache.sql_cache_short.type=memory
beaker.cache.sql_cache_short.expire=10
beaker.cache.sql_cache_short.key_length = 256

beaker.cache.sql_cache_med.type=memory
beaker.cache.sql_cache_med.expire=360
beaker.cache.sql_cache_med.key_length = 256

beaker.cache.sql_cache_long.type=file
beaker.cache.sql_cache_long.expire=3600
beaker.cache.sql_cache_long.key_length = 256
<%text>
####################################
###       BEAKER SESSION        ####
####################################
## Type of storage used for the session, current types are 
## dbm, file, memcached, database, and memory. 
## The storage uses the Container API 
## that is also used by the cache system.
</%text>
<%text>## db session ##</%text>
#beaker.session.type = ext:database
#beaker.session.sa.url = postgresql://postgres:qwe@localhost/rhodecode
#beaker.session.table_name = db_session 

<%text>## encrypted cookie client side session, good for many instances ##</%text>
#beaker.session.type = cookie

<%text>## file based cookies (default) ##</%text>
#beaker.session.type = file

beaker.session.key = rhodecode
beaker.session.secret = ${uuid()}

<%text>## Secure encrypted cookie. Requires AES and AES python libraries</%text>
<%text>## you must disable beaker.session.secret to use this</%text>
#beaker.session.encrypt_key = <key_for_encryption>
#beaker.session.validate_key = <validation_key>

<%text>## sets session as invalid if it haven't been accessed for given amount of time</%text>
beaker.session.timeout = 2592000
beaker.session.httponly = true
#beaker.session.cookie_path = /<your-prefix>

<%text>## uncomment for https secure cookie</%text>
beaker.session.secure = false

<%text>## auto save the session to not to use .save()</%text>
beaker.session.auto = False

<%text>## default cookie expiration time in seconds `true` expire at browser close ##</%text>
#beaker.session.cookie_expires = 3600

%if error_aggregation_service == 'errormator':
<%text>
############################
## ERROR HANDLING SYSTEMS ##
############################

####################
### [errormator] ###
####################

## Errormator is tailored to work with RhodeCode, see 
## http://errormator.com for details how to obtain an account
## you must install python package `errormator_client` to make it work
</%text>
<%text>## errormator enabled</%text>
errormator = false

errormator.server_url = https://api.errormator.com
errormator.api_key = YOUR_API_KEY

<%text>## TWEAK AMOUNT OF INFO SENT HERE</%text>

<%text>## enables 404 error logging (default False)</%text>
errormator.report_404 = false

<%text>## time in seconds after request is considered being slow (default 1)</%text>
errormator.slow_request_time = 1

<%text>## record slow requests in application</%text>
<%text>## (needs to be enabled for slow datastore recording and time tracking)</%text>
errormator.slow_requests = true

<%text>## enable hooking to application loggers</%text>
# errormator.logging = true

<%text>## minimum log level for log capture</%text>
# errormator.logging.level = WARNING

<%text>## send logs only from erroneous/slow requests</%text>
<%text>## (saves API quota for intensive logging)</%text>
errormator.logging_on_error = false

<%text>## list of additonal keywords that should be grabbed from environ object</%text>
<%text>## can be string with comma separated list of words in lowercase</%text>
<%text>## (by default client will always send following info:</%text>
<%text>## 'REMOTE_USER', 'REMOTE_ADDR', 'SERVER_NAME', 'CONTENT_TYPE' + all keys that</%text>
<%text>## start with HTTP* this list be extended with additional keywords here</%text>
errormator.environ_keys_whitelist = 


<%text>## list of keywords that should be blanked from request object</%text>
<%text>## can be string with comma separated list of words in lowercase</%text>
<%text>## (by default client will always blank keys that contain following words</%text>
<%text>## 'password', 'passwd', 'pwd', 'auth_tkt', 'secret', 'csrf'</%text>
<%text>## this list be extended with additional keywords set here</%text>
errormator.request_keys_blacklist =


<%text>## list of namespaces that should be ignores when gathering log entries</%text>
<%text>## can be string with comma separated list of namespaces</%text>
<%text>## (by default the client ignores own entries: errormator_client.client)</%text>
errormator.log_namespace_blacklist =  
%elif error_aggregation_service == 'sentry':
<%text>
################
### [sentry] ###
################

## sentry is a alternative open source error aggregator
## you must install python packages `sentry` and `raven` to enable 
</%text>
sentry.dsn = YOUR_DNS
sentry.servers =
sentry.name =
sentry.key =
sentry.public_key =
sentry.secret_key =
sentry.project =
sentry.site =
sentry.include_paths =
sentry.exclude_paths =
%endif
<%text>
################################################################################
## WARNING: *THE LINE BELOW MUST BE UNCOMMENTED ON A PRODUCTION ENVIRONMENT*  ##
## Debug mode will enable the interactive debugging tool, allowing ANYONE to  ##
## execute malicious code after an exception is raised.                       ##
################################################################################
</%text>
set debug = false
<%text>
##################################
###       LOGVIEW CONFIG       ###
##################################
</%text>
logview.sqlalchemy = #faa
logview.pylons.templating = #bfb
logview.pylons.util = #eee
<%text>
#########################################################
### DB CONFIGS - EACH DB WILL HAVE IT'S OWN CONFIG    ###
#########################################################
</%text>
%if database_engine == 'sqlite':
# SQLITE [default]
sqlalchemy.db1.url = sqlite:///${here}/rhodecode.db?timeout=60
%elif database_engine == 'postgres':
# POSTGRESQL
sqlalchemy.db1.url = postgresql://user:pass@localhost/rhodecode
%elif database_engine == 'mysql':
# MySQL
sqlalchemy.db1.url = mysql://user:pass@localhost/rhodecode
%endif
# see sqlalchemy docs for others

sqlalchemy.db1.echo = false
sqlalchemy.db1.pool_recycle = 3600
sqlalchemy.db1.convert_unicode = true
<%text>
################################
### LOGGING CONFIGURATION   ####
################################
</%text>
[loggers]
keys = root, routes, rhodecode, sqlalchemy, beaker, templates, whoosh_indexer

[handlers]
keys = console, console_sql

[formatters]
keys = generic, color_formatter, color_formatter_sql
<%text>
#############
## LOGGERS ##
#############
</%text>
[logger_root]
level = NOTSET
handlers = console

[logger_routes]
level = DEBUG
handlers = 
qualname = routes.middleware
<%text>## "level = DEBUG" logs the route matched and routing variables.</%text>
propagate = 1

[logger_beaker]
level = DEBUG
handlers = 
qualname = beaker.container
propagate = 1

[logger_templates]
level = INFO
handlers = 
qualname = pylons.templating
propagate = 1

[logger_rhodecode]
level = DEBUG
handlers = 
qualname = rhodecode
propagate = 1

[logger_sqlalchemy]
level = INFO
handlers = console_sql
qualname = sqlalchemy.engine
propagate = 0

[logger_whoosh_indexer]
level = DEBUG
handlers = 
qualname = whoosh_indexer
propagate = 1
<%text>
##############
## HANDLERS ##
##############
</%text>
[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = INFO
formatter = generic

[handler_console_sql]
class = StreamHandler
args = (sys.stderr,)
level = WARN
formatter = generic
<%text>
################
## FORMATTERS ##
################
</%text>
[formatter_generic]
format = %(asctime)s.%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %Y-%m-%d %H:%M:%S

[formatter_color_formatter]
class=rhodecode.lib.colored_formatter.ColorFormatter
format= %(asctime)s.%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %Y-%m-%d %H:%M:%S

[formatter_color_formatter_sql]
class=rhodecode.lib.colored_formatter.ColorFormatterSql
format= %(asctime)s.%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %Y-%m-%d %H:%M:%S
