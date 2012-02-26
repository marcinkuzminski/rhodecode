import rhodecode
from rhodecode.lib.utils import BasePasterCommand, Command
from celery.app import app_or_default
from celery.bin import camqadm, celerybeat, celeryd, celeryev

from rhodecode.lib import str2bool

__all__ = ['CeleryDaemonCommand', 'CeleryBeatCommand',
           'CAMQPAdminCommand', 'CeleryEventCommand']


class CeleryCommand(BasePasterCommand):
    """Abstract class implements run methods needed for celery

    Starts the celery worker that uses a paste.deploy configuration
    file.
    """

    def update_parser(self):
        """
        Abstract method.  Allows for the class's parser to be updated
        before the superclass's `run` method is called.  Necessary to
        allow options/arguments to be passed through to the underlying
        celery command.
        """

        cmd = self.celery_command(app_or_default())
        for x in cmd.get_options():
            self.parser.add_option(x)

    def command(self):
        from pylons import config
        try:
            CELERY_ON = str2bool(config['app_conf'].get('use_celery'))
        except KeyError:
            CELERY_ON = False

        if CELERY_ON == False:
            raise Exception('Please enable celery_on in .ini config '
                            'file before running celeryd')
        rhodecode.CELERY_ON = CELERY_ON
        cmd = self.celery_command(app_or_default())
        return cmd.run(**vars(self.options))

class CeleryDaemonCommand(CeleryCommand):
    """Start the celery worker

    Starts the celery worker that uses a paste.deploy configuration
    file.
    """
    usage = 'CONFIG_FILE [celeryd options...]'
    summary = __doc__.splitlines()[0]
    description = "".join(__doc__.splitlines()[2:])

    parser = Command.standard_parser(quiet=True)
    celery_command = celeryd.WorkerCommand


class CeleryBeatCommand(CeleryCommand):
    """Start the celery beat server

    Starts the celery beat server using a paste.deploy configuration
    file.
    """
    usage = 'CONFIG_FILE [celerybeat options...]'
    summary = __doc__.splitlines()[0]
    description = "".join(__doc__.splitlines()[2:])

    parser = Command.standard_parser(quiet=True)
    celery_command = celerybeat.BeatCommand


class CAMQPAdminCommand(CeleryCommand):
    """CAMQP Admin

    CAMQP celery admin tool.
    """
    usage = 'CONFIG_FILE [camqadm options...]'
    summary = __doc__.splitlines()[0]
    description = "".join(__doc__.splitlines()[2:])

    parser = Command.standard_parser(quiet=True)
    celery_command = camqadm.AMQPAdminCommand

class CeleryEventCommand(CeleryCommand):
    """Celery event command.

    Capture celery events.
    """
    usage = 'CONFIG_FILE [celeryev options...]'
    summary = __doc__.splitlines()[0]
    description = "".join(__doc__.splitlines()[2:])

    parser = Command.standard_parser(quiet=True)
    celery_command = celeryev.EvCommand
