"""
Hg app, a web based mercurial repository managment based on pylons
"""

VERSION = (0, 7, 4, 'beta')

__version__ = '.'.join((str(each) for each in VERSION[:4]))

def get_version():
    """
    Returns shorter version (digit parts only) as string.
    """
    return '.'.join((str(each) for each in VERSION[:3]))
