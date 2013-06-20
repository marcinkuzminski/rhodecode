import os
import sys
from paste.script.appinstall import AbstractInstallCommand
from paste.script.command import BadCommand
from paste.deploy import appconfig

# fix rhodecode import
from os.path import dirname as dn
rc_path = dn(dn(dn(os.path.realpath(__file__))))
sys.path.append(rc_path)


class Command(AbstractInstallCommand):

    default_verbosity = 1
    max_args = 1
    min_args = 1
    summary = "Setup an application, given a config file"
    usage = "CONFIG_FILE"
    group_name = "RhodeCode"

    description = """\

    Setup RhodeCode according to its configuration file.  This is
    the second part of a two-phase web application installation
    process (the first phase is prepare-app).  The setup process
    consist of things like setting up databases, creating super user
    """

    parser = AbstractInstallCommand.standard_parser(
        simulate=True, quiet=True, interactive=True)
    parser.add_option('--user',
                      action='store',
                      dest='username',
                      default=None,
                      help='Admin Username')
    parser.add_option('--email',
                      action='store',
                      dest='email',
                      default=None,
                      help='Admin Email')
    parser.add_option('--password',
                      action='store',
                      dest='password',
                      default=None,
                      help='Admin password min 6 chars')
    parser.add_option('--repos',
                      action='store',
                      dest='repos_location',
                      default=None,
                      help='Absolute path to repositories location')
    parser.add_option('--name',
                      action='store',
                      dest='section_name',
                      default=None,
                      help='The name of the section to set up (default: app:main)')
    parser.add_option('--force-yes',
                       action='store_true',
                       dest='force_ask',
                       default=None,
                       help='Force yes to every question')
    parser.add_option('--force-no',
                       action='store_false',
                       dest='force_ask',
                       default=None,
                       help='Force no to every question')
    parser.add_option('--public-access',
                       action='store_true',
                       dest='public_access',
                       default=None,
                       help='Enable public access on this installation (default)')
    parser.add_option('--no-public-access',
                       action='store_false',
                       dest='public_access',
                       default=None,
                       help='Disable public access on this installation ')
    def command(self):
        config_spec = self.args[0]
        section = self.options.section_name
        if section is None:
            if '#' in config_spec:
                config_spec, section = config_spec.split('#', 1)
            else:
                section = 'main'
        if not ':' in section:
            plain_section = section
            section = 'app:' + section
        else:
            plain_section = section.split(':', 1)[0]
        if not config_spec.startswith('config:'):
            config_spec = 'config:' + config_spec
        if plain_section != 'main':
            config_spec += '#' + plain_section
        config_file = config_spec[len('config:'):].split('#', 1)[0]
        config_file = os.path.join(os.getcwd(), config_file)
        self.logging_file_config(config_file)
        conf = appconfig(config_spec, relative_to=os.getcwd())
        ep_name = conf.context.entry_point_name
        ep_group = conf.context.protocol
        dist = conf.context.distribution
        if dist is None:
            raise BadCommand(
                "The section %r is not the application (probably a filter).  "
                "You should add #section_name, where section_name is the "
                "section that configures your application" % plain_section)
        installer = self.get_installer(dist, ep_group, ep_name)
        installer.setup_config(
            self, config_file, section, self.sysconfig_install_vars(installer))
        self.call_sysconfig_functions(
            'post_setup_hook', installer, config_file)
