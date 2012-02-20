"""
Various utilities to work with Python < 2.7.

Those utilities may be deleted once ``vcs`` stops support for older Python
versions.
"""
import sys


if sys.version_info >= (2, 7):
    unittest = __import__('unittest')
else:
    unittest = __import__('unittest2')
