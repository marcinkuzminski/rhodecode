import sys
from rhodecode import get_version
from rhodecode import __platform__
from rhodecode import __license__
from rhodecode import PLATFORM_OTHERS

py_version = sys.version_info

if py_version < (2, 5):
    raise Exception('RhodeCode requires python 2.5 or later')

requirements = [
        "Pylons==1.0.0",
        "Beaker==1.5.4",
        "WebHelpers>=1.2",
        "formencode==1.2.4",
        "SQLAlchemy==0.7.3",
        "Mako==0.5.0",
        "pygments>=1.4",
        "mercurial>=1.9.3,<2.0",
        "whoosh<1.8",
        "celery>=2.2.5,<2.3",
        "babel",
        "python-dateutil>=1.5.0,<2.0.0",
        "dulwich>=0.8.0,<0.9.0",
        "vcs>=0.2.3.dev",
        "webob==1.1.1"
    ]

dependency_links = [
    "https://secure.rhodecode.org/vcs/archive/default.zip#egg=vcs-0.2.2.dev",
    "https://bitbucket.org/marcinkuzminski/vcs/get/default.zip#egg=vcs-0.2.2.dev",
]

classifiers = ['Development Status :: 4 - Beta',
               'Environment :: Web Environment',
               'Framework :: Pylons',
               'Intended Audience :: Developers',
               'License :: OSI Approved :: GNU General Public License (GPL)',
               'Operating System :: OS Independent',
               'Programming Language :: Python',
               'Programming Language :: Python :: 2.5',
               'Programming Language :: Python :: 2.6',
               'Programming Language :: Python :: 2.7', ]

if py_version < (2, 6):
    requirements.append("simplejson")
    requirements.append("pysqlite")

if __platform__ in PLATFORM_OTHERS:
    requirements.append("py-bcrypt")


#additional files from project that goes somewhere in the filesystem
#relative to sys.prefix
data_files = []

#additional files that goes into package itself
package_data = {'rhodecode': ['i18n/*/LC_MESSAGES/*.mo', ], }

description = ('Mercurial repository browser/management with '
               'build in push/pull server and full text search')
keywords = ' '.join(['rhodecode', 'rhodiumcode', 'mercurial', 'git',
                      'repository management', 'hgweb replacement'
                      'hgwebdir', 'gitweb replacement', 'serving hgweb', ])
#long description
try:
    readme_file = 'README.rst'
    changelog_file = 'docs/changelog.rst'
    long_description = open(readme_file).read() + '\n\n' + \
        open(changelog_file).read()

except IOError, err:
    sys.stderr.write("[WARNING] Cannot find file specified as "
        "long_description (%s)\n or changelog (%s) skipping that file" \
            % (readme_file, changelog_file))
    long_description = description


try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages
#packages
packages = find_packages(exclude=['ez_setup'])

setup(
    name='RhodeCode',
    version=get_version(),
    description=description,
    long_description=long_description,
    keywords=keywords,
    license=__license__,
    author='Marcin Kuzminski',
    author_email='marcin@python-works.com',
    dependency_links=dependency_links,
    url='http://rhodecode.org',
    install_requires=requirements,
    classifiers=classifiers,
    setup_requires=["PasteScript>=1.6.3"],
    data_files=data_files,
    packages=packages,
    include_package_data=True,
    test_suite='nose.collector',
    package_data=package_data,
    message_extractors={'rhodecode': [
            ('**.py', 'python', None),
            ('templates/**.mako', 'mako', {'input_encoding': 'utf-8'}),
            ('templates/**.html', 'mako', {'input_encoding': 'utf-8'}),
            ('public/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['PasteScript', 'Pylons'],
    entry_points="""
    [paste.app_factory]
    main = rhodecode.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller

    [paste.global_paster_command]
    make-index = rhodecode.lib.indexers:MakeIndex
    upgrade-db = rhodecode.lib.dbmigrate:UpgradeDb
    celeryd=rhodecode.lib.celerypylons.commands:CeleryDaemonCommand
    """,
)
