# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Utilities for dealing with stuff in unittest."""


import sys

__metaclass__ = type
__all__ = [
    'iterate_tests',
    ]


if sys.version_info > (3, 0):
    def _u(s):
        """Replacement for u'some string' in Python 3."""
        return s
    def _b(s):
        """A byte literal."""
        return s.encode("latin-1")
    advance_iterator = next
    def istext(x):
        return isinstance(x, str)
    def classtypes():
        return (type,)
else:
    def _u(s):
        return unicode(s, "latin-1")
    def _b(s):
        return s
    advance_iterator = lambda it: it.next()
    def istext(x):
        return isinstance(x, basestring)
    def classtypes():
        import types
        return (type, types.ClassType)


def iterate_tests(test_suite_or_case):
    """Iterate through all of the test cases in 'test_suite_or_case'."""
    try:
        suite = iter(test_suite_or_case)
    except TypeError:
        yield test_suite_or_case
    else:
        for test in suite:
            for subtest in iterate_tests(test):
                yield subtest
