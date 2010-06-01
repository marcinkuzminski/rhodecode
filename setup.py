from pylons_app import get_version
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='pylons_app',
    version=get_version(),
    description='',
    author='marcin kuzminski',
    author_email='marcin@python-works.com',
    url='',
    install_requires=[
        "Pylons>=1.0.0",
        "SQLAlchemy>=0.6",
        "Mako>=0.3.2",
        "vcs>=0.1.2",
        "pygments>=1.3.0"
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
