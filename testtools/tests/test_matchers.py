# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Tests for matchers."""

import doctest

from testtools import (
    Matcher, # check that Matcher is exposed at the top level for docs.
    TestCase,
    )
from testtools.matchers import (
    DocTestMatches,
    )


class TestDocTestMatchesInterface(TestCase):

    def test_matches_match(self):
        matcher = DocTestMatches("Ran 1 test in ...s", doctest.ELLIPSIS)
        matches = ["Ran 1 test in 0.000s", "Ran 1 test in 1.234s"]
        mismatches = ["Ran 1 tests in 0.000s", "Ran 2 test in 0.000s"]
        for candidate in matches:
            self.assertEqual(None, matcher.match(candidate))
        for candidate in mismatches:
            mismatch = matcher.match(candidate)
            self.assertNotEqual(None, mismatch)
            self.assertNotEqual(None, getattr(mismatch, 'describe', None))

    def test__str__(self):
        # [(expected, object to __str__)].
        examples = [("DocTestMatches('Ran 1 test in ...s\\n')",
            DocTestMatches("Ran 1 test in ...s")),
            ("DocTestMatches('foo\\n', flags=8)", DocTestMatches("foo", flags=8)),
            ]
        for expected, matcher in examples:
            self.assertThat(matcher, DocTestMatches(expected))

    def test_describe_difference(self):
        # [(expected, matchee, matcher), ...]
        examples = [('Expected:\n    Ran 1 tests in ...s\nGot:\n'
            '    Ran 1 test in 0.123s\n', "Ran 1 test in 0.123s",
            DocTestMatches("Ran 1 tests in ...s", doctest.ELLIPSIS))]
        for difference, matchee, matcher in examples:
            mismatch = matcher.match(matchee)
            self.assertEqual(difference, mismatch.describe())


class TestDocTestMatchesSpecific(TestCase):

    def test___init__simple(self):
        matcher = DocTestMatches("foo")
        self.assertEqual("foo\n", matcher.want)

    def test___init__flags(self):
        matcher = DocTestMatches("bar\n", doctest.ELLIPSIS)
        self.assertEqual("bar\n", matcher.want)
        self.assertEqual(doctest.ELLIPSIS, matcher.flags)


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
