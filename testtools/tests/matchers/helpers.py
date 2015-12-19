# Copyright (c) 2008-2015 testtools developers. See LICENSE for details.

import collections
from testtools.compat import text
from testtools.matchers._imatcher import IMatcher, IMismatch
from testtools.tests.helpers import FullStackRunTest


class TestMatchersInterface(object):
    """Show that a matcher implements the matcher interface correctly.

    :ivar matches_matcher: An instance of the matcher being tested.
    :ivar matches_matches: An iterable of things that match the instance.
    :ivar matches_mismatches: An iterable of things that do *not* match the
        instance.
    :ivar str_examples: An iterable of (string, matcher), where ``string`` is
        the expected result of ``str(matcher)``.
    :ivar describe_examples: An iterable of (text, candidate, matcher), where
        ``text`` is the expected description of the mismatch resulting from
        matching ``candidate`` against ``matcher``.
    """

    run_tests_with = FullStackRunTest

    def _iter_matchers(self):
        """Iterate through matchers from the sample data."""
        yield self.matches_matcher
        for _, matcher in self.str_examples:
            yield matcher
        for _, _, matcher in self.describe_examples:
            yield matcher

    def _iter_mismatches(self):
        """Iterate through mismatches from the sample data."""
        # Don't iterate through matches_mismatches, because sometimes they are
        # iter() and are thus mutated by other tests.
        for _, matchee, matcher in self.describe_examples:
            yield matcher.match(matchee)

    def assert_provides(self, interface, obj):
        """Assert ``obj`` provides ``interface``."""
        # TODO: Provide a matcher for this.
        self.assertTrue(
            interface.providedBy(obj),
            '%s not provided by %r' % (interface, obj))

    def assert_matcher(self, matcher):
        """Assert that ``matcher`` provides ``IMatcher``."""
        # TODO: Provide ValidMatcher() matcher that does this.
        self.assert_provides(IMatcher, matcher)

    def assert_mismatch(self, mismatch):
        """Assert that ``mismatch`` provides ``IMismatch``."""
        # TODO: Provide ValidMismatch() matcher that does this.
        self.assert_provides(IMismatch, mismatch)
        description = mismatch.describe()
        self.assertTrue(
            isinstance(description, text),
            "Description is not text, is %r instead: %r" % (
                type(description), description))
        details = mismatch.get_details()
        self.assertTrue(
            isinstance(details, collections.Mapping),
            "details are not a map, are %r instead: %r" % (
                type(details), details))
        # TODO: In a follow-up branch, add an interface for content, and
        # assert that the details all implement that interface.

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
        for mismatch in self._iter_mismatches():
            details = mismatch.get_details()
            self.assertEqual(dict(details), details)

    def test_matcher_provides_interface(self):
        # The matcher provides the IMatcher interface.
        for matcher in self._iter_matchers():
            self.assert_matcher(matcher)

    def test_mismatches_provide_interface(self):
        # Mismatches provide the IMismatch interface.
        for mismatch in self._iter_mismatches():
            self.assert_mismatch(mismatch)
