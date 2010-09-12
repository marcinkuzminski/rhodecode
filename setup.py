from pylons_app import get_version
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='HgApp-%s'%get_version(),
    version=get_version(),
    description='Mercurial repository serving and browsing app',
    keywords='mercurial web hgwebdir replacement serving hgweb',
    license='BSD',
    author='marcin kuzminski',
    author_email='marcin@python-works.com',
    url='http://hg.python-works.com',
    install_requires=[
        "Pylons>=1.0.0",
        "SQLAlchemy>=0.6",
        "babel",
        "Mako>=0.3.2",
        "vcs>=0.1.4",
        "pygments>=1.3.0",
        "mercurial>=1.6",
        "pysqlite",
        "whoosh==1.0.0b10",
        "py-bcrypt",
        "celery",
    ],
    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'pylons_app': ['i18n/*/LC_MESSAGES/*.mo']},
    message_extractors={'pylons_app': [
            ('**.py', 'python', None),
            ('templates/**.mako', 'mako', {'input_encoding': 'utf-8'}),
            ('public/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['PasteScript', 'Pylons'],
    entry_points="""
    [paste.app_factory]
    main = pylons_app.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
