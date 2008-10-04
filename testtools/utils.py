# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Utilities for dealing with stuff in unittest."""

__metaclass__ = type
__all__ = [
    'iterate_tests',
    ]


def iterate_tests(test_suite_or_case):
    """Iterate through all of the test cases in `test_suite_or_case`."""
    try:
        suite = iter(test_suite_or_case)
    except TypeError:
        yield test_suite_or_case
    else:
        for test in suite:
            for subtest in iterate_tests(test):
                yield subtest
