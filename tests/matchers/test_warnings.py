# Copyright (c) 2008-2016 testtools developers. See LICENSE for details.

import warnings
from typing import ClassVar

from testtools import TestCase
from testtools.matchers import (
    AfterPreprocessing,
    Contains,
    Equals,
    HasLength,
    MatchesListwise,
    MatchesStructure,
)
from testtools.matchers._warnings import IsDeprecated, WarningMessage, Warnings

from ..helpers import FullStackRunTest
from ..matchers.helpers import TestMatchersInterface


def make_warning(warning_type, message):
    warnings.warn(message, warning_type, 2)


def make_warning_message(message, category, filename=None, lineno=None, line=None):
    return warnings.WarningMessage(
        message=message, category=category, filename=filename, lineno=lineno, line=line
    )


class TestWarningMessageCategoryTypeInterface(TestCase, TestMatchersInterface):
    """Tests for `testtools.matchers._warnings.WarningMessage`.

    In particular matching the ``category_type``.
    """

    matches_matcher: ClassVar = WarningMessage(category_type=DeprecationWarning)
    warning_foo = make_warning_message("foo", DeprecationWarning)
    warning_bar = make_warning_message("bar", SyntaxWarning)
    warning_base = make_warning_message("base", Warning)
    matches_matches: ClassVar = [warning_foo]
    matches_mismatches: ClassVar = [warning_bar, warning_base]

    str_examples: ClassVar[list] = []
    describe_examples: ClassVar[list] = []


class TestWarningMessageMessageInterface(TestCase, TestMatchersInterface):
    """Tests for `testtools.matchers._warnings.WarningMessage`.

    In particular matching the ``message``.
    """

    matches_matcher: ClassVar = WarningMessage(
        category_type=DeprecationWarning, message=Equals("foo")
    )
    warning_foo = make_warning_message("foo", DeprecationWarning)
    warning_bar = make_warning_message("bar", DeprecationWarning)
    matches_matches: ClassVar = [warning_foo]
    matches_mismatches: ClassVar = [warning_bar]

    str_examples: ClassVar[list] = []
    describe_examples: ClassVar[list] = []


class TestWarningMessageFilenameInterface(TestCase, TestMatchersInterface):
    """Tests for `testtools.matchers._warnings.WarningMessage`.

    In particular matching the ``filename``.
    """

    matches_matcher: ClassVar = WarningMessage(
        category_type=DeprecationWarning, filename=Equals("a")
    )
    warning_foo = make_warning_message("foo", DeprecationWarning, filename="a")
    warning_bar = make_warning_message("bar", DeprecationWarning, filename="b")
    matches_matches: ClassVar = [warning_foo]
    matches_mismatches: ClassVar = [warning_bar]

    str_examples: ClassVar[list] = []
    describe_examples: ClassVar[list] = []


class TestWarningMessageLineNumberInterface(TestCase, TestMatchersInterface):
    """Tests for `testtools.matchers._warnings.WarningMessage`.

    In particular matching the ``lineno``.
    """

    matches_matcher: ClassVar = WarningMessage(
        category_type=DeprecationWarning, lineno=Equals(42)
    )
    warning_foo = make_warning_message("foo", DeprecationWarning, lineno=42)
    warning_bar = make_warning_message("bar", DeprecationWarning, lineno=21)
    matches_matches: ClassVar = [warning_foo]
    matches_mismatches: ClassVar = [warning_bar]

    str_examples: ClassVar[list] = []
    describe_examples: ClassVar[list] = []


class TestWarningMessageLineInterface(TestCase, TestMatchersInterface):
    """Tests for `testtools.matchers._warnings.WarningMessage`.

    In particular matching the ``line``.
    """

    matches_matcher: ClassVar = WarningMessage(
        category_type=DeprecationWarning, line=Equals("x")
    )
    warning_foo = make_warning_message("foo", DeprecationWarning, line="x")
    warning_bar = make_warning_message("bar", DeprecationWarning, line="y")
    matches_matches: ClassVar = [warning_foo]
    matches_mismatches: ClassVar = [warning_bar]

    str_examples: ClassVar[list] = []
    describe_examples: ClassVar[list] = []


class TestWarningsInterface(TestCase, TestMatchersInterface):
    """Tests for `testtools.matchers._warnings.Warnings`.

    Specifically without the optional argument.
    """

    matches_matcher: ClassVar = Warnings()

    @staticmethod
    def old_func():
        warnings.warn("old_func is deprecated", DeprecationWarning, 2)

    matches_matches: ClassVar = [old_func]
    matches_mismatches: ClassVar = [lambda: None]

    # Tricky to get function objects to render constantly, and the interfaces
    # helper uses assertEqual rather than (for instance) DocTestMatches.
    str_examples: ClassVar[list] = []

    describe_examples: ClassVar[list] = []


class TestWarningsMatcherInterface(TestCase, TestMatchersInterface):
    """Tests for `testtools.matchers._warnings.Warnings`.

    Specifically with the optional matcher argument.
    """

    matches_matcher: ClassVar = Warnings(
        warnings_matcher=MatchesListwise(
            [MatchesStructure(message=AfterPreprocessing(str, Contains("old_func")))]
        )
    )

    @staticmethod
    def old_func():
        warnings.warn("old_func is deprecated", DeprecationWarning, 2)

    @staticmethod
    def older_func():
        warnings.warn("older_func is deprecated", DeprecationWarning, 2)

    matches_matches: ClassVar = [old_func]
    matches_mismatches: ClassVar = [lambda: None, older_func]

    str_examples: ClassVar[list] = []
    describe_examples: ClassVar[list] = []


class TestWarningsMatcherNoWarningsInterface(TestCase, TestMatchersInterface):
    """Tests for `testtools.matchers._warnings.Warnings`.

    Specifically with the optional matcher argument matching that there were no
    warnings.
    """

    matches_matcher: ClassVar = Warnings(warnings_matcher=HasLength(0))

    @staticmethod
    def nowarning_func():
        pass

    @staticmethod
    def warning_func():
        warnings.warn("warning_func is deprecated", DeprecationWarning, 2)

    matches_matches: ClassVar = [nowarning_func]
    matches_mismatches: ClassVar = [warning_func]

    str_examples: ClassVar[list] = []
    describe_examples: ClassVar[list] = []


class TestWarningMessage(TestCase):
    """Tests for `testtools.matchers._warnings.WarningMessage`."""

    run_tests_with = FullStackRunTest

    def test_category(self):
        def old_func():
            warnings.warn("old_func is deprecated", DeprecationWarning, 2)

        self.assertThat(old_func, IsDeprecated(Contains("old_func")))


class TestIsDeprecated(TestCase):
    """Tests for `testtools.matchers._warnings.IsDeprecated`."""

    run_tests_with = FullStackRunTest

    def test_warning(self):
        def old_func():
            warnings.warn("old_func is deprecated", DeprecationWarning, 2)

        self.assertThat(old_func, IsDeprecated(Contains("old_func")))


def test_suite():
    from unittest import TestLoader

    return TestLoader().loadTestsFromName(__name__)
