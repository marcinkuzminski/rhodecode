from rhodecode import get_version


requirements = [
        "Pylons>=1.0.0",
        "SQLAlchemy>=0.6",
        "babel",
        "Mako>=0.3.2",
        "vcs>=0.1.7",
        "pygments>=1.3.0",
        "mercurial>=1.6",
        "pysqlite",
        "whoosh==1.0.0",
        "py-bcrypt",
        "celery",
    ]

#additional files for project
data_files = [
              ('init.d', ['init.d/rhodecode-daemon',
                          'init.d/rhodecode-daemon2',
                          'init.d/celeryd']),
              ('', ['celeryconfig.py', 'production.ini', 'development.ini']),
              ]


long_description = '\n' + open('README.rst').read()

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='RhodeCode',
    version=get_version(),
    description='Mercurial repository serving and browsing app',
    long_description=long_description,
    keywords='mercurial web hgwebdir replacement serving hgweb rhodecode',
    license='BSD',
    author='Marcin Kuzminski',
    author_email='marcin@python-works.com',
    url='http://hg.python-works.com',
    install_requires=requirements,
    setup_requires=["PasteScript>=1.6.3"],
    data_files=data_files,
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'rhodecode': ['i18n/*/LC_MESSAGES/*.mo']},
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
    """,
)
