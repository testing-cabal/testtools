# Copyright (c) 2008-2012 testtools developers. See LICENSE for details.

import re
from typing import ClassVar

from testtools import TestCase
from testtools.compat import (
    _b,
    text_repr,
)
from testtools.matchers._basic import (
    Contains,
    DoesNotEndWith,
    DoesNotStartWith,
    EndsWith,
    Equals,
    GreaterThan,
    HasLength,
    Is,
    IsInstance,
    LessThan,
    MatchesRegex,
    NotEquals,
    SameMembers,
    StartsWith,
    _BinaryMismatch,
)
from testtools.tests.helpers import FullStackRunTest
from testtools.tests.matchers.helpers import TestMatchersInterface


class Test_BinaryMismatch(TestCase):
    """Mismatches from binary comparisons need useful describe output"""

    _long_string = "This is a longish multiline non-ascii string\n\xa7"
    _long_b = _b(_long_string)
    _long_u = _long_string

    class CustomRepr:
        def __init__(self, repr_string):
            self._repr_string = repr_string

        def __repr__(self):
            return "<object " + self._repr_string + ">"

    def test_short_objects(self):
        o1, o2 = self.CustomRepr("a"), self.CustomRepr("b")
        mismatch = _BinaryMismatch(o1, "!~", o2)
        self.assertEqual(mismatch.describe(), f"{o1!r} !~ {o2!r}")

    def test_short_mixed_strings(self):
        b, u = _b("\xa7"), "\xa7"
        mismatch = _BinaryMismatch(b, "!~", u)
        self.assertEqual(mismatch.describe(), f"{b!r} !~ {u!r}")

    def test_long_bytes(self):
        one_line_b = self._long_b.replace(_b("\n"), _b(" "))
        mismatch = _BinaryMismatch(one_line_b, "!~", self._long_b)
        self.assertEqual(
            mismatch.describe(),
            "{}:\nreference = {}\nactual    = {}\n".format(
                "!~",
                text_repr(self._long_b, multiline=True),
                text_repr(one_line_b),
            ),
        )

    def test_long_unicode(self):
        one_line_u = self._long_u.replace("\n", " ")
        mismatch = _BinaryMismatch(one_line_u, "!~", self._long_u)
        self.assertEqual(
            mismatch.describe(),
            "{}:\nreference = {}\nactual    = {}\n".format(
                "!~",
                text_repr(self._long_u, multiline=True),
                text_repr(one_line_u),
            ),
        )

    def test_long_mixed_strings(self):
        mismatch = _BinaryMismatch(self._long_b, "!~", self._long_u)
        self.assertEqual(
            mismatch.describe(),
            "{}:\nreference = {}\nactual    = {}\n".format(
                "!~",
                text_repr(self._long_u, multiline=True),
                text_repr(self._long_b, multiline=True),
            ),
        )

    def test_long_bytes_and_object(self):
        obj = object()
        mismatch = _BinaryMismatch(self._long_b, "!~", obj)
        self.assertEqual(
            mismatch.describe(),
            "{}:\nreference = {}\nactual    = {}\n".format(
                "!~",
                repr(obj),
                text_repr(self._long_b, multiline=True),
            ),
        )

    def test_long_unicode_and_object(self):
        obj = object()
        mismatch = _BinaryMismatch(self._long_u, "!~", obj)
        self.assertEqual(
            mismatch.describe(),
            "{}:\nreference = {}\nactual    = {}\n".format(
                "!~",
                repr(obj),
                text_repr(self._long_u, multiline=True),
            ),
        )


class TestEqualsInterface(TestCase, TestMatchersInterface):
    matches_matcher: ClassVar = Equals(1)
    matches_matches: ClassVar = [1]
    matches_mismatches: ClassVar = [2]

    str_examples: ClassVar = [
        ("Equals(1)", Equals(1)),
        ("Equals('1')", Equals("1")),
    ]

    describe_examples: ClassVar = [
        ("2 != 1", 2, Equals(1)),
        (
            (
                "!=:\n"
                "reference = 'abcdefghijklmnopqrstuvwxyz0123456789'\n"
                "actual    = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'\n"
            ),
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            Equals("abcdefghijklmnopqrstuvwxyz0123456789"),
        ),
    ]


class TestNotEqualsInterface(TestCase, TestMatchersInterface):
    matches_matcher: ClassVar = NotEquals(1)
    matches_matches: ClassVar = [2]
    matches_mismatches: ClassVar = [1]

    str_examples: ClassVar = [
        ("NotEquals(1)", NotEquals(1)),
        ("NotEquals('1')", NotEquals("1")),
    ]

    describe_examples: ClassVar = [("1 == 1", 1, NotEquals(1))]


class TestIsInterface(TestCase, TestMatchersInterface):
    foo = object()
    bar = object()

    matches_matcher: ClassVar = Is(foo)
    matches_matches: ClassVar = [foo]
    matches_mismatches: ClassVar = [bar, 1]

    str_examples: ClassVar = [("Is(2)", Is(2))]

    describe_examples: ClassVar = [("2 is not 1", 2, Is(1))]


class TestIsInstanceInterface(TestCase, TestMatchersInterface):
    class Foo:
        pass

    matches_matcher: ClassVar = IsInstance(Foo)
    matches_matches: ClassVar = [Foo()]
    matches_mismatches: ClassVar = [object(), 1, Foo]

    str_examples: ClassVar = [
        ("IsInstance(str)", IsInstance(str)),
        ("IsInstance(str, int)", IsInstance(str, int)),
    ]

    describe_examples: ClassVar = [
        ("'foo' is not an instance of int", "foo", IsInstance(int)),
        (
            "'foo' is not an instance of any of (int, type)",
            "foo",
            IsInstance(int, type),
        ),
    ]


class TestLessThanInterface(TestCase, TestMatchersInterface):
    matches_matcher: ClassVar = LessThan(4)
    matches_matches: ClassVar = [-5, 3]
    matches_mismatches: ClassVar = [4, 5, 5000]

    str_examples: ClassVar = [
        ("LessThan(12)", LessThan(12)),
    ]

    describe_examples: ClassVar = [
        ("5 >= 4", 5, LessThan(4)),
        ("4 >= 4", 4, LessThan(4)),
    ]


class TestGreaterThanInterface(TestCase, TestMatchersInterface):
    matches_matcher: ClassVar = GreaterThan(4)
    matches_matches: ClassVar = [5, 8]
    matches_mismatches: ClassVar = [-2, 0, 4]

    str_examples: ClassVar = [
        ("GreaterThan(12)", GreaterThan(12)),
    ]

    describe_examples: ClassVar = [
        ("4 <= 5", 4, GreaterThan(5)),
        ("4 <= 4", 4, GreaterThan(4)),
    ]


class TestContainsInterface(TestCase, TestMatchersInterface):
    matches_matcher: ClassVar = Contains("foo")
    matches_matches: ClassVar = ["foo", "afoo", "fooa"]
    matches_mismatches: ClassVar = ["f", "fo", "oo", "faoo", "foao"]

    str_examples: ClassVar = [
        ("Contains(1)", Contains(1)),
        ("Contains('foo')", Contains("foo")),
    ]

    describe_examples: ClassVar = [("1 not in 2", 2, Contains(1))]


class DoesNotStartWithTests(TestCase):
    run_tests_with = FullStackRunTest

    def test_describe(self):
        mismatch = DoesNotStartWith("fo", "bo")
        self.assertEqual("'fo' does not start with 'bo'.", mismatch.describe())

    def test_describe_non_ascii_unicode(self):
        string = "A\xa7"
        suffix = "B\xa7"
        mismatch = DoesNotStartWith(string, suffix)
        self.assertEqual(
            f"{text_repr(string)} does not start with {text_repr(suffix)}.",
            mismatch.describe(),
        )

    def test_describe_non_ascii_bytes(self):
        string = _b("A\xa7")
        suffix = _b("B\xa7")
        mismatch = DoesNotStartWith(string, suffix)
        self.assertEqual(
            f"{string!r} does not start with {suffix!r}.", mismatch.describe()
        )


class StartsWithTests(TestCase):
    run_tests_with = FullStackRunTest

    def test_str(self):
        matcher = StartsWith("bar")
        self.assertEqual("StartsWith('bar')", str(matcher))

    def test_str_with_bytes(self):
        b = _b("\xa7")
        matcher = StartsWith(b)
        self.assertEqual(f"StartsWith({b!r})", str(matcher))

    def test_str_with_unicode(self):
        u = "\xa7"
        matcher = StartsWith(u)
        self.assertEqual(f"StartsWith({u!r})", str(matcher))

    def test_match(self):
        matcher = StartsWith("bar")
        self.assertIs(None, matcher.match("barf"))

    def test_mismatch_returns_does_not_start_with(self):
        matcher = StartsWith("bar")
        self.assertIsInstance(matcher.match("foo"), DoesNotStartWith)

    def test_mismatch_sets_matchee(self):
        matcher = StartsWith("bar")
        mismatch = matcher.match("foo")
        self.assertEqual("foo", mismatch.matchee)

    def test_mismatch_sets_expected(self):
        matcher = StartsWith("bar")
        mismatch = matcher.match("foo")
        self.assertEqual("bar", mismatch.expected)


class DoesNotEndWithTests(TestCase):
    run_tests_with = FullStackRunTest

    def test_describe(self):
        mismatch = DoesNotEndWith("fo", "bo")
        self.assertEqual("'fo' does not end with 'bo'.", mismatch.describe())

    def test_describe_non_ascii_unicode(self):
        string = "A\xa7"
        suffix = "B\xa7"
        mismatch = DoesNotEndWith(string, suffix)
        self.assertEqual(
            f"{text_repr(string)} does not end with {text_repr(suffix)}.",
            mismatch.describe(),
        )

    def test_describe_non_ascii_bytes(self):
        string = _b("A\xa7")
        suffix = _b("B\xa7")
        mismatch = DoesNotEndWith(string, suffix)
        self.assertEqual(
            f"{string!r} does not end with {suffix!r}.", mismatch.describe()
        )


class EndsWithTests(TestCase):
    run_tests_with = FullStackRunTest

    def test_str(self):
        matcher = EndsWith("bar")
        self.assertEqual("EndsWith('bar')", str(matcher))

    def test_str_with_bytes(self):
        b = _b("\xa7")
        matcher = EndsWith(b)
        self.assertEqual(f"EndsWith({b!r})", str(matcher))

    def test_str_with_unicode(self):
        u = "\xa7"
        matcher = EndsWith(u)
        self.assertEqual(f"EndsWith({u!r})", str(matcher))

    def test_match(self):
        matcher = EndsWith("arf")
        self.assertIs(None, matcher.match("barf"))

    def test_mismatch_returns_does_not_end_with(self):
        matcher = EndsWith("bar")
        self.assertIsInstance(matcher.match("foo"), DoesNotEndWith)

    def test_mismatch_sets_matchee(self):
        matcher = EndsWith("bar")
        mismatch = matcher.match("foo")
        self.assertEqual("foo", mismatch.matchee)

    def test_mismatch_sets_expected(self):
        matcher = EndsWith("bar")
        mismatch = matcher.match("foo")
        self.assertEqual("bar", mismatch.expected)


class TestSameMembers(TestCase, TestMatchersInterface):
    matches_matcher: ClassVar = SameMembers([1, 1, 2, 3, {"foo": "bar"}])
    matches_matches: ClassVar = [
        [1, 1, 2, 3, {"foo": "bar"}],
        [3, {"foo": "bar"}, 1, 2, 1],
        [3, 2, 1, {"foo": "bar"}, 1],
        (2, {"foo": "bar"}, 3, 1, 1),
    ]
    matches_mismatches: ClassVar = [
        {1, 2, 3},
        [1, 1, 2, 3, 5],
        [1, 2, 3, {"foo": "bar"}],
        "foo",
    ]

    describe_examples: ClassVar = [
        (
            (
                "elements differ:\n"
                "reference = ['apple', 'orange', 'canteloupe', 'watermelon', "
                "'lemon', 'banana']\n"
                "actual    = ['orange', 'apple', 'banana', 'sparrow', "
                "'lemon', 'canteloupe']\n"
                ": \n"
                "missing:    ['watermelon']\n"
                "extra:      ['sparrow']"
            ),
            [
                "orange",
                "apple",
                "banana",
                "sparrow",
                "lemon",
                "canteloupe",
            ],
            SameMembers(
                [
                    "apple",
                    "orange",
                    "canteloupe",
                    "watermelon",
                    "lemon",
                    "banana",
                ]
            ),
        ),
    ]

    str_examples: ClassVar = [
        ("SameMembers([1, 2, 3])", SameMembers([1, 2, 3])),
    ]


class TestMatchesRegex(TestCase, TestMatchersInterface):
    matches_matcher: ClassVar = MatchesRegex("a|b")
    matches_matches: ClassVar = ["a", "b"]
    matches_mismatches: ClassVar = ["c"]

    str_examples: ClassVar = [
        ("MatchesRegex('a|b')", MatchesRegex("a|b")),
        ("MatchesRegex('a|b', re.M)", MatchesRegex("a|b", re.M)),
        ("MatchesRegex('a|b', re.I|re.M)", MatchesRegex("a|b", re.I | re.M)),
        ("MatchesRegex({!r})".format(_b("\xa7")), MatchesRegex(_b("\xa7"))),
        ("MatchesRegex({!r})".format("\xa7"), MatchesRegex("\xa7")),
    ]

    describe_examples: ClassVar = [
        ("'c' does not match /a|b/", "c", MatchesRegex("a|b")),
        ("'c' does not match /a\\d/", "c", MatchesRegex(r"a\d")),
        (
            "{!r} does not match /\\s+\\xa7/".format(_b("c")),
            _b("c"),
            MatchesRegex(_b("\\s+\xa7")),
        ),
        ("{!r} does not match /\\s+\\xa7/".format("c"), "c", MatchesRegex("\\s+\xa7")),
    ]


class TestHasLength(TestCase, TestMatchersInterface):
    matches_matcher: ClassVar = HasLength(2)
    matches_matches: ClassVar = [[1, 2]]
    matches_mismatches: ClassVar = [[], [1], [3, 2, 1]]

    str_examples: ClassVar = [
        ("HasLength(2)", HasLength(2)),
    ]

    describe_examples: ClassVar = [
        ("len([]) != 1", [], HasLength(1)),
    ]


def test_suite():
    from unittest import TestLoader

    return TestLoader().loadTestsFromName(__name__)
