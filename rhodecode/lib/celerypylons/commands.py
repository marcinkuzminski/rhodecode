import os
from paste.script.command import Command, BadCommand
import paste.deploy
from pylons import config


__all__ = ['CeleryDaemonCommand', 'CeleryBeatCommand',
           'CAMQPAdminCommand', 'CeleryEventCommand']


class CeleryCommand(Command):
    """
    Abstract Base Class for celery commands.

    The celery commands are somewhat aggressive about loading
    celery.conf, and since our module sets the `CELERY_LOADER`
    environment variable to our loader, we have to bootstrap a bit and
    make sure we've had a chance to load the pylons config off of the
    command line, otherwise everything fails.
    """
    min_args = 1
    min_args_error = "Please provide a paster config file as an argument."
    takes_config_file = 1
    requires_config_file = True

    def run(self, args):
        """
        Overrides Command.run
        
        Checks for a config file argument and loads it.
        """
        if len(args) < self.min_args:
            raise BadCommand(
                self.min_args_error % {'min_args': self.min_args,
                                       'actual_args': len(args)})
        # Decrement because we're going to lob off the first argument.
        # @@ This is hacky
        self.min_args -= 1
        self.bootstrap_config(args[0])
        self.update_parser()
        return super(CeleryCommand, self).run(args[1:])

    def update_parser(self):
        """
        Abstract method.  Allows for the class's parser to be updated
        before the superclass's `run` method is called.  Necessary to
        allow options/arguments to be passed through to the underlying
        celery command.
        """
        raise NotImplementedError("Abstract Method.")

    def bootstrap_config(self, conf):
        """
        Loads the pylons configuration.
        """
        path_to_ini_file = os.path.realpath(conf)
        conf = paste.deploy.appconfig('config:' + path_to_ini_file)
        config.init_app(conf.global_conf, conf.local_conf)


class CeleryDaemonCommand(CeleryCommand):
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


class CeleryBeatCommand(CeleryCommand):
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

class CAMQPAdminCommand(CeleryCommand):
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


class CeleryEventCommand(CeleryCommand):
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
