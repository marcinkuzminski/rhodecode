# List of modules to import when celery starts.
import sys
import os
import ConfigParser
root = os.getcwd()

PYLONS_CONFIG_NAME = 'development.ini'

sys.path.append(root)
config = ConfigParser.ConfigParser({'here':root})
config.read('%s/%s' % (root, PYLONS_CONFIG_NAME))
PYLONS_CONFIG = config

CELERY_IMPORTS = ("pylons_app.lib.celerylib.tasks",)

## Result store settings.
CELERY_RESULT_BACKEND = "database"
CELERY_RESULT_DBURI = dict(config.items('app:main'))['sqlalchemy.db1.url']
CELERY_RESULT_SERIALIZER = 'json'


BROKER_CONNECTION_MAX_RETRIES = 30

## Broker settings.
BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_VHOST = "rabbitmqhost"
BROKER_USER = "rabbitmq"
BROKER_PASSWORD = "qweqwe"

## Worker settings
## If you're doing mostly I/O you can have more processes,
## but if mostly spending CPU, try to keep it close to the
## number of CPUs on your machine. If not set, the number of CPUs/cores
## available will be used.
CELERYD_CONCURRENCY = 2
# CELERYD_LOG_FILE = "celeryd.log"
CELERYD_LOG_LEVEL = "DEBUG"
CELERYD_MAX_TASKS_PER_CHILD = 3

#Tasks will never be sent to the queue, but executed locally instead.
CELERY_ALWAYS_EAGER = False

#===============================================================================
# EMAIL SETTINGS
#===============================================================================
pylons_email_config = dict(config.items('DEFAULT'))

CELERY_SEND_TASK_ERROR_EMAILS = True

#List of (name, email_address) tuples for the admins that should receive error e-mails.
ADMINS = [('Administrator', pylons_email_config.get('email_to'))]

#The e-mail address this worker sends e-mails from. Default is "celery@localhost".
SERVER_EMAIL = pylons_email_config.get('error_email_from')

#The mail server to use. Default is "localhost".
MAIL_HOST = pylons_email_config.get('smtp_server')

#Username (if required) to log on to the mail server with.
MAIL_HOST_USER = pylons_email_config.get('smtp_username')

#Password (if required) to log on to the mail server with.
MAIL_HOST_PASSWORD = pylons_email_config.get('smtp_password')

MAIL_PORT = pylons_email_config.get('smtp_port')


#===============================================================================
# INSTRUCTIONS FOR RABBITMQ
#===============================================================================
# rabbitmqctl add_user rabbitmq qweqwe
# rabbitmqctl add_vhost rabbitmqhost
# rabbitmqctl set_permissions -p rabbitmqhost rabbitmq ".*" ".*" ".*"
