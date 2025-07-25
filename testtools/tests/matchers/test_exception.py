# Copyright (c) 2008-2012 testtools developers. See LICENSE for details.

import sys
from typing import ClassVar

from testtools import TestCase
from testtools.matchers import (
    AfterPreprocessing,
    Equals,
)
from testtools.matchers._exception import (
    MatchesException,
    Raises,
    raises,
)
from testtools.tests.helpers import FullStackRunTest
from testtools.tests.matchers.helpers import TestMatchersInterface


def make_error(type, *args, **kwargs):
    try:
        raise type(*args, **kwargs)
    except type:
        return sys.exc_info()


class TestMatchesExceptionInstanceInterface(TestCase, TestMatchersInterface):
    matches_matcher = MatchesException(ValueError("foo"))
    error_foo = make_error(ValueError, "foo")
    error_bar = make_error(ValueError, "bar")
    error_base_foo = make_error(Exception, "foo")
    matches_matches: ClassVar[list] = [error_foo]
    matches_mismatches: ClassVar[list] = [error_bar, error_base_foo]

    _e = ""

    str_examples: ClassVar[list] = [
        (
            f"MatchesException(Exception('foo'{_e}))",
            MatchesException(Exception("foo")),
        )
    ]
    describe_examples: ClassVar[list] = [
        (
            f"{Exception!r} is not a {ValueError!r}",
            error_base_foo,
            MatchesException(ValueError("foo")),
        ),
        (
            f"ValueError('bar'{_e}) has different arguments to ValueError('foo'{_e}).",
            error_bar,
            MatchesException(ValueError("foo")),
        ),
    ]


class TestMatchesExceptionTypeInterface(TestCase, TestMatchersInterface):
    matches_matcher = MatchesException(ValueError)
    error_foo = make_error(ValueError, "foo")
    error_sub = make_error(UnicodeError, "bar")
    error_base_foo = make_error(Exception, "foo")
    matches_matches: ClassVar[list] = [error_foo, error_sub]
    matches_mismatches: ClassVar[list] = [error_base_foo]

    str_examples: ClassVar[list] = [
        (f"MatchesException({Exception!r})", MatchesException(Exception))
    ]
    describe_examples: ClassVar[list] = [
        (
            f"{Exception!r} is not a {ValueError!r}",
            error_base_foo,
            MatchesException(ValueError),
        ),
    ]


class TestMatchesExceptionTypeReInterface(TestCase, TestMatchersInterface):
    matches_matcher = MatchesException(ValueError, "fo.")
    error_foo = make_error(ValueError, "foo")
    error_sub = make_error(UnicodeError, "foo")
    error_bar = make_error(ValueError, "bar")
    matches_matches: ClassVar[list] = [error_foo, error_sub]
    matches_mismatches: ClassVar[list] = [error_bar]

    str_examples: ClassVar[list] = [
        (f"MatchesException({Exception!r})", MatchesException(Exception, "fo."))
    ]
    describe_examples: ClassVar[list] = [
        ("'bar' does not match /fo./", error_bar, MatchesException(ValueError, "fo.")),
    ]


class TestMatchesExceptionTypeMatcherInterface(TestCase, TestMatchersInterface):
    matches_matcher = MatchesException(
        ValueError, AfterPreprocessing(str, Equals("foo"))
    )
    error_foo = make_error(ValueError, "foo")
    error_sub = make_error(UnicodeError, "foo")
    error_bar = make_error(ValueError, "bar")
    matches_matches: ClassVar[list] = [error_foo, error_sub]
    matches_mismatches: ClassVar[list] = [error_bar]

    str_examples: ClassVar[list] = [
        (f"MatchesException({Exception!r})", MatchesException(Exception, Equals("foo")))
    ]
    describe_examples: ClassVar[list] = [
        (f"{error_bar[1]!r} != 5", error_bar, MatchesException(ValueError, Equals(5))),
    ]


class TestRaisesInterface(TestCase, TestMatchersInterface):
    matches_matcher = Raises()

    def boom():
        raise Exception("foo")

    matches_matches: ClassVar[list] = [boom]
    matches_mismatches: ClassVar[list] = [lambda: None]

    # Tricky to get function objects to render constantly, and the interfaces
    # helper uses assertEqual rather than (for instance) DocTestMatches.
    str_examples: ClassVar[list] = []

    describe_examples: ClassVar[list] = []


class TestRaisesExceptionMatcherInterface(TestCase, TestMatchersInterface):
    matches_matcher = Raises(exception_matcher=MatchesException(Exception("foo")))

    def boom_bar():
        raise Exception("bar")

    def boom_foo():
        raise Exception("foo")

    matches_matches: ClassVar[list] = [boom_foo]
    matches_mismatches: ClassVar[list] = [lambda: None, boom_bar]

    # Tricky to get function objects to render constantly, and the interfaces
    # helper uses assertEqual rather than (for instance) DocTestMatches.
    str_examples: ClassVar[list] = []

    describe_examples: ClassVar[list] = []


class TestRaisesBaseTypes(TestCase):
    run_tests_with = FullStackRunTest

    def raiser(self):
        raise KeyboardInterrupt("foo")

    def test_KeyboardInterrupt_matched(self):
        # When KeyboardInterrupt is matched, it is swallowed.
        matcher = Raises(MatchesException(KeyboardInterrupt))
        self.assertThat(self.raiser, matcher)

    def test_KeyboardInterrupt_propagates(self):
        # The default 'it raised' propagates KeyboardInterrupt.
        match_keyb = Raises(MatchesException(KeyboardInterrupt))

        def raise_keyb_from_match():
            matcher = Raises()
            matcher.match(self.raiser)

        self.assertThat(raise_keyb_from_match, match_keyb)

    def test_KeyboardInterrupt_match_Exception_propagates(self):
        # If the raised exception isn't matched, and it is not a subclass of
        # Exception, it is propagated.
        match_keyb = Raises(MatchesException(KeyboardInterrupt))

        def raise_keyb_from_match():
            matcher = Raises(MatchesException(Exception))
            matcher.match(self.raiser)

        self.assertThat(raise_keyb_from_match, match_keyb)


class TestRaisesConvenience(TestCase):
    run_tests_with = FullStackRunTest

    def test_exc_type(self):
        self.assertThat(lambda: 1 / 0, raises(ZeroDivisionError))

    def test_exc_value(self):
        e = RuntimeError("You lose!")

        def raiser():
            raise e

        self.assertThat(raiser, raises(e))


def test_suite():
    from unittest import TestLoader

    return TestLoader().loadTestsFromName(__name__)
