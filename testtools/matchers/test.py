# Copyright (c) 2008-2012 testtools developers. See LICENSE for details.

from collections.abc import Callable
from typing import Any, ClassVar

from testtools.matchers._impl import Matcher


class TestMatchersInterface:
    """Mixin class that provides test methods for matcher interfaces."""

    __test__ = False  # Tell pytest not to collect this as a test class

    matches_matcher: ClassVar[Matcher[Any]]
    matches_matches: ClassVar[list[Any]]
    matches_mismatches: ClassVar[list[Any]]
    str_examples: ClassVar[Any]
    describe_examples: ClassVar[Any]

    assertEqual: Callable[..., Any]
    assertNotEqual: Callable[..., Any]
    assertThat: Callable[..., Any]

    def test_matches_match(self) -> None:
        matcher = self.matches_matcher
        matches = self.matches_matches
        mismatches = self.matches_mismatches
        for candidate in matches:
            self.assertEqual(None, matcher.match(candidate))
        for candidate in mismatches:
            mismatch = matcher.match(candidate)
            self.assertNotEqual(None, mismatch)
            self.assertNotEqual(None, getattr(mismatch, "describe", None))

    def test__str__(self) -> None:
        # [(expected, object to __str__)].
        from testtools.matchers._doctest import DocTestMatches

        examples = self.str_examples
        for expected, matcher in examples:
            self.assertThat(matcher, DocTestMatches(expected))

    def test_describe_difference(self) -> None:
        # [(expected, matchee, matcher), ...]
        examples = self.describe_examples
        for difference, matchee, matcher in examples:
            mismatch = matcher.match(matchee)
            self.assertEqual(difference, mismatch.describe())

    def test_mismatch_details(self) -> None:
        # The mismatch object must provide get_details, which must return a
        # dictionary mapping names to Content objects.
        examples = self.describe_examples
        for difference, matchee, matcher in examples:
            mismatch = matcher.match(matchee)
            details = mismatch.get_details()
            self.assertEqual(dict(details), details)
