# Copyright (c) 2008-2012 testtools developers. See LICENSE for details.

from collections.abc import Callable
from typing import Any, ClassVar, Protocol, runtime_checkable


@runtime_checkable
class MatcherTestProtocol(Protocol):
    """Protocol for test classes that test matchers."""

    matches_matcher: ClassVar[Any]
    matches_matches: ClassVar[Any]
    matches_mismatches: ClassVar[Any]
    str_examples: ClassVar[Any]
    describe_examples: ClassVar[Any]
    assertEqual: Callable[..., Any]
    assertNotEqual: Callable[..., Any]
    assertThat: Callable[..., Any]


class TestMatchersInterface:
    """Mixin class that provides test methods for matcher interfaces."""

    def test_matches_match(self: MatcherTestProtocol) -> None:
        matcher = self.matches_matcher
        matches = self.matches_matches
        mismatches = self.matches_mismatches
        for candidate in matches:
            self.assertEqual(None, matcher.match(candidate))
        for candidate in mismatches:
            mismatch = matcher.match(candidate)
            self.assertNotEqual(None, mismatch)
            self.assertNotEqual(None, getattr(mismatch, "describe", None))

    def test__str__(self: MatcherTestProtocol) -> None:
        # [(expected, object to __str__)].
        from testtools.matchers._doctest import DocTestMatches

        examples = self.str_examples
        for expected, matcher in examples:
            self.assertThat(matcher, DocTestMatches(expected))

    def test_describe_difference(self: MatcherTestProtocol) -> None:
        # [(expected, matchee, matcher), ...]
        examples = self.describe_examples
        for difference, matchee, matcher in examples:
            mismatch = matcher.match(matchee)
            self.assertEqual(difference, mismatch.describe())

    def test_mismatch_details(self: MatcherTestProtocol) -> None:
        # The mismatch object must provide get_details, which must return a
        # dictionary mapping names to Content objects.
        examples = self.describe_examples
        for difference, matchee, matcher in examples:
            mismatch = matcher.match(matchee)
            details = mismatch.get_details()
            self.assertEqual(dict(details), details)
