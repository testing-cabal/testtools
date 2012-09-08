# Copyright (c) 2008-2011 testtools developers. See LICENSE for details.

"""Tests for matchers."""

from testtools import (
    Matcher, # check that Matcher is exposed at the top level for docs.
    TestCase,
    )
from testtools.compat import (
    str_is_unicode,
    text_repr,
    _u,
    )
from testtools.matchers import (
    Equals,
    MatchesException,
    MatchesPredicate,
    Mismatch,
    MismatchDecorator,
    MismatchError,
    Raises,
    )
from testtools.tests.helpers import FullStackRunTest

# Silence pyflakes.
Matcher


class TestMismatch(TestCase):

    run_tests_with = FullStackRunTest

    def test_constructor_arguments(self):
        mismatch = Mismatch("some description", {'detail': "things"})
        self.assertEqual("some description", mismatch.describe())
        self.assertEqual({'detail': "things"}, mismatch.get_details())

    def test_constructor_no_arguments(self):
        mismatch = Mismatch()
        self.assertThat(mismatch.describe,
            Raises(MatchesException(NotImplementedError)))
        self.assertEqual({}, mismatch.get_details())


class TestMismatchError(TestCase):

    def test_is_assertion_error(self):
        # MismatchError is an AssertionError, so that most of the time, it
        # looks like a test failure, rather than an error.
        def raise_mismatch_error():
            raise MismatchError(2, Equals(3), Equals(3).match(2))
        self.assertRaises(AssertionError, raise_mismatch_error)

    def test_default_description_is_mismatch(self):
        mismatch = Equals(3).match(2)
        e = MismatchError(2, Equals(3), mismatch)
        self.assertEqual(mismatch.describe(), str(e))

    def test_default_description_unicode(self):
        matchee = _u('\xa7')
        matcher = Equals(_u('a'))
        mismatch = matcher.match(matchee)
        e = MismatchError(matchee, matcher, mismatch)
        self.assertEqual(mismatch.describe(), str(e))

    def test_verbose_description(self):
        matchee = 2
        matcher = Equals(3)
        mismatch = matcher.match(2)
        e = MismatchError(matchee, matcher, mismatch, True)
        expected = (
            'Match failed. Matchee: %r\n'
            'Matcher: %s\n'
            'Difference: %s\n' % (
                matchee,
                matcher,
                matcher.match(matchee).describe(),
                ))
        self.assertEqual(expected, str(e))

    def test_verbose_unicode(self):
        # When assertThat is given matchees or matchers that contain non-ASCII
        # unicode strings, we can still provide a meaningful error.
        matchee = _u('\xa7')
        matcher = Equals(_u('a'))
        mismatch = matcher.match(matchee)
        expected = (
            'Match failed. Matchee: %s\n'
            'Matcher: %s\n'
            'Difference: %s\n' % (
                text_repr(matchee),
                matcher,
                mismatch.describe(),
                ))
        e = MismatchError(matchee, matcher, mismatch, True)
        if str_is_unicode:
            actual = str(e)
        else:
            actual = unicode(e)
            # Using str() should still work, and return ascii only
            self.assertEqual(
                expected.replace(matchee, matchee.encode("unicode-escape")),
                str(e).decode("ascii"))
        self.assertEqual(expected, actual)


class TestMatchersInterface(object):

    run_tests_with = FullStackRunTest

    def test_matches_match(self):
        matcher = self.matches_matcher
        matches = self.matches_matches
        mismatches = self.matches_mismatches
        for candidate in matches:
            self.assertEqual(None, matcher.match(candidate))
        for candidate in mismatches:
            mismatch = matcher.match(candidate)
            self.assertNotEqual(None, mismatch)
            self.assertNotEqual(None, getattr(mismatch, 'describe', None))

    def test__str__(self):
        # [(expected, object to __str__)].
        from testtools.matchers._doctest import DocTestMatches
        examples = self.str_examples
        for expected, matcher in examples:
            self.assertThat(matcher, DocTestMatches(expected))

    def test_describe_difference(self):
        # [(expected, matchee, matcher), ...]
        examples = self.describe_examples
        for difference, matchee, matcher in examples:
            mismatch = matcher.match(matchee)
            self.assertEqual(difference, mismatch.describe())

    def test_mismatch_details(self):
        # The mismatch object must provide get_details, which must return a
        # dictionary mapping names to Content objects.
        examples = self.describe_examples
        for difference, matchee, matcher in examples:
            mismatch = matcher.match(matchee)
            details = mismatch.get_details()
            self.assertEqual(dict(details), details)


class TestMismatchDecorator(TestCase):

    run_tests_with = FullStackRunTest

    def test_forwards_description(self):
        x = Mismatch("description", {'foo': 'bar'})
        decorated = MismatchDecorator(x)
        self.assertEqual(x.describe(), decorated.describe())

    def test_forwards_details(self):
        x = Mismatch("description", {'foo': 'bar'})
        decorated = MismatchDecorator(x)
        self.assertEqual(x.get_details(), decorated.get_details())

    def test_repr(self):
        x = Mismatch("description", {'foo': 'bar'})
        decorated = MismatchDecorator(x)
        self.assertEqual(
            '<testtools.matchers.MismatchDecorator(%r)>' % (x,),
            repr(decorated))


def is_even(x):
    return x % 2 == 0


class TestMatchesPredicate(TestCase, TestMatchersInterface):

    matches_matcher = MatchesPredicate(is_even, "%s is not even")
    matches_matches = [2, 4, 6, 8]
    matches_mismatches = [3, 5, 7, 9]

    str_examples = [
        ("MatchesPredicate(%r, %r)" % (is_even, "%s is not even"),
         MatchesPredicate(is_even, "%s is not even")),
        ]

    describe_examples = [
        ('7 is not even', 7, MatchesPredicate(is_even, "%s is not even")),
        ]


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
