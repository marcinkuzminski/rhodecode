import sys
py_version = sys.version_info

from rhodecode import get_version

requirements = [
        "Pylons==1.0.0",
        "WebHelpers==1.2",
        "SQLAlchemy==0.6.5",
        "Mako==0.3.6",
        "vcs==0.1.10",
        "pygments==1.3.1",
        "mercurial==1.7.2",
        "whoosh==1.3.4",
        "celery==2.1.4",
        "py-bcrypt",
        "babel",
    ]

classifiers = ['Development Status :: 5 - Production/Stable',
               'Environment :: Web Environment',
               'Framework :: Pylons',
               'Intended Audience :: Developers',
               'License :: OSI Approved :: BSD License',
               'Operating System :: OS Independent',
               'Programming Language :: Python', ]

if sys.version_info < (2, 6):
    requirements.append("simplejson")
    requirements.append("pysqlite")

#additional files from project that goes somewhere in the filesystem
#relative to sys.prefix
data_files = []

#additional files that goes into package itself
package_data = {'rhodecode': ['i18n/*/LC_MESSAGES/*.mo', ], }

description = ('Mercurial repository browser/management with '
               'build in push/pull server and full text search')
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
    keywords='rhodiumcode mercurial web hgwebdir gitweb git replacement serving hgweb rhodecode',
    license='BSD',
    author='Marcin Kuzminski',
    author_email='marcin@python-works.com',
    url='http://hg.python-works.com',
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
    celerybeat=rhodecode.lib.celerypylons.commands:CeleryBeatCommand
    camqadm=rhodecode.lib.celerypylons.commands:CAMQPAdminCommand
    celeryev=rhodecode.lib.celerypylons.commands:CeleryEventCommand
              
    """,
)
