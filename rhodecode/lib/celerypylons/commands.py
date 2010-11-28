from rhodecode.lib.utils import BasePasterCommand, Command


__all__ = ['CeleryDaemonCommand', 'CeleryBeatCommand',
           'CAMQPAdminCommand', 'CeleryEventCommand']


class CeleryDaemonCommand(BasePasterCommand):
    """Start the celery worker

    Starts the celery worker that uses a paste.deploy configuration
    file.
    """
    usage = 'CONFIG_FILE [celeryd options...]'
    summary = __doc__.splitlines()[0]
    description = "".join(__doc__.splitlines()[2:])

    parser = Command.standard_parser(quiet=True)

    def update_parser(self):
        from celery.bin import celeryd
        for x in celeryd.WorkerCommand().get_options():
            self.parser.add_option(x)

    def command(self):
        from celery.bin import celeryd
        return celeryd.WorkerCommand().run(**vars(self.options))


class CeleryBeatCommand(BasePasterCommand):
    """Start the celery beat server

    Starts the celery beat server using a paste.deploy configuration
    file.
    """
    usage = 'CONFIG_FILE [celerybeat options...]'
    summary = __doc__.splitlines()[0]
    description = "".join(__doc__.splitlines()[2:])

    parser = Command.standard_parser(quiet=True)

    def update_parser(self):
        from celery.bin import celerybeat
        for x in celerybeat.BeatCommand().get_options():
            self.parser.add_option(x)

    def command(self):
        from celery.bin import celerybeat
        return celerybeat.BeatCommand(**vars(self.options))

class CAMQPAdminCommand(BasePasterCommand):
    """CAMQP Admin

    CAMQP celery admin tool.
    """
    usage = 'CONFIG_FILE [camqadm options...]'
    summary = __doc__.splitlines()[0]
    description = "".join(__doc__.splitlines()[2:])

    parser = Command.standard_parser(quiet=True)

    def update_parser(self):
        from celery.bin import camqadm
        for x in camqadm.OPTION_LIST:
            self.parser.add_option(x)

    def command(self):
        from celery.bin import camqadm
        return camqadm.camqadm(*self.args, **vars(self.options))


class CeleryEventCommand(BasePasterCommand):
    """Celery event commandd.

    Capture celery events.
    """
    usage = 'CONFIG_FILE [celeryev options...]'
    summary = __doc__.splitlines()[0]
    description = "".join(__doc__.splitlines()[2:])

    parser = Command.standard_parser(quiet=True)

    def update_parser(self):
        from celery.bin import celeryev
        for x in celeryev.OPTION_LIST:
            self.parser.add_option(x)

    def command(self):
        from celery.bin import celeryev
        return celeryev.run_celeryev(**vars(self.options))
