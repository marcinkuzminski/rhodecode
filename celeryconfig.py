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
CELERYD_MAX_TASKS_PER_CHILD = 1

#CELERY_ALWAYS_EAGER = True
#rabbitmqctl add_user rabbitmq qweqwe
#rabbitmqctl add_vhost rabbitmqhost
#rabbitmqctl set_permissions -p rabbitmqhost rabbitmq ".*" ".*" ".*"
