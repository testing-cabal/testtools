# Copyright (c) 2016 testtools developers. See LICENSE for details.

from testtools import TestCase
from testtools.compat import _u
from testtools.matchers import always, never
from testtools.tests.matchers.helpers import TestMatchersInterface


class TestAlwaysInterface(TestMatchersInterface, TestCase):
    """:py:func:`~testtools.matchers.always` always matches."""
    matches_matcher = always()
    matches_matches = [42, object(), 'hi mom']
    matches_mismatches = []

    str_examples = [('always()', always())]
    describe_examples = []


class TestNeverInterface(TestMatchersInterface, TestCase):
    """:py:func:`~testtools.matchers.never` never matches."""
    matches_matcher = never()
    matches_matches = []
    matches_mismatches = [42, object(), 'hi mom']

    str_examples = [('never()', never())]
    describe_examples = [(_u('Inevitable mismatch on 42'), 42, never())]


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
