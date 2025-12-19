from typing import ClassVar

from testtools import TestCase
from testtools.matchers import (
    Equals,
    Not,
    NotEquals,
)
from testtools.matchers._dict import (
    ContainedByDict,
    ContainsDict,
    KeysEqual,
    MatchesAllDict,
    MatchesDict,
    _SubDictOf,
)

from ..matchers.helpers import TestMatchersInterface


class TestMatchesAllDictInterface(TestCase, TestMatchersInterface):
    matches_matcher: ClassVar = MatchesAllDict({"a": NotEquals(1), "b": NotEquals(2)})
    matches_matches: ClassVar = [3, 4]
    matches_mismatches: ClassVar = [1, 2]

    str_examples: ClassVar = [
        ("MatchesAllDict({'a': NotEquals(1), 'b': NotEquals(2)})", matches_matcher)
    ]

    describe_examples: ClassVar = [
        ("""a: 1 == 1""", 1, matches_matcher),
    ]


class TestKeysEqualEmpty(TestCase, TestMatchersInterface):
    matches_matcher: ClassVar = KeysEqual()
    matches_matches: ClassVar[list] = [
        {},
    ]
    matches_mismatches: ClassVar = [
        {"foo": 0, "bar": 1},
        {"foo": 0},
        {"bar": 1},
        {"foo": 0, "bar": 1, "baz": 2},
        {"a": None, "b": None, "c": None},
    ]

    str_examples: ClassVar = [
        ("KeysEqual()", KeysEqual()),
    ]

    describe_examples: ClassVar = [
        ("[] does not match {1: 2}: Keys not equal", {1: 2}, matches_matcher),
    ]


class TestKeysEqualWithList(TestCase, TestMatchersInterface):
    matches_matcher: ClassVar = KeysEqual("foo", "bar")
    matches_matches: ClassVar = [
        {"foo": 0, "bar": 1},
    ]
    matches_mismatches: ClassVar = [
        {},
        {"foo": 0},
        {"bar": 1},
        {"foo": 0, "bar": 1, "baz": 2},
        {"a": None, "b": None, "c": None},
    ]

    str_examples: ClassVar = [
        ("KeysEqual('foo', 'bar')", KeysEqual("foo", "bar")),
    ]

    describe_examples: ClassVar[list] = []

    def test_description(self):
        matchee = {"foo": 0, "bar": 1, "baz": 2}
        mismatch = KeysEqual("foo", "bar").match(matchee)
        description = mismatch.describe()
        self.assertThat(
            description,
            Equals(f"['bar', 'foo'] does not match {matchee!r}: Keys not equal"),
        )


class TestKeysEqualWithDict(TestKeysEqualWithList):
    matches_matcher: ClassVar = KeysEqual({"foo": 3, "bar": 4})


class TestSubDictOf(TestCase, TestMatchersInterface):
    matches_matcher: ClassVar = _SubDictOf({"foo": "bar", "baz": "qux"})

    matches_matches: ClassVar = [
        {"foo": "bar", "baz": "qux"},
        {"foo": "bar"},
    ]

    matches_mismatches: ClassVar = [
        {"foo": "bar", "baz": "qux", "cat": "dog"},
        {"foo": "bar", "cat": "dog"},
    ]

    str_examples: ClassVar[list] = []
    describe_examples: ClassVar[list] = []


class TestMatchesDict(TestCase, TestMatchersInterface):
    matches_matcher: ClassVar = MatchesDict(
        {"foo": Equals("bar"), "baz": Not(Equals("qux"))}
    )

    matches_matches: ClassVar = [
        {"foo": "bar", "baz": None},
        {"foo": "bar", "baz": "quux"},
    ]
    matches_mismatches: ClassVar = [
        {},
        {"foo": "bar", "baz": "qux"},
        {"foo": "bop", "baz": "qux"},
        {"foo": "bar", "baz": "quux", "cat": "dog"},
        {"foo": "bar", "cat": "dog"},
    ]

    str_examples: ClassVar = [
        (
            "MatchesDict({{'baz': {}, 'foo': {}}})".format(
                Not(Equals("qux")), Equals("bar")
            ),
            matches_matcher,
        ),
    ]

    describe_examples: ClassVar = [
        (
            "Missing: {\n  'baz': Not(Equals('qux')),\n  'foo': Equals('bar'),\n}",
            {},
            matches_matcher,
        ),
        (
            "Differences: {\n  'baz': 'qux' matches Equals('qux'),\n}",
            {"foo": "bar", "baz": "qux"},
            matches_matcher,
        ),
        (
            "Differences: {\n"
            "  'baz': 'qux' matches Equals('qux'),\n"
            "  'foo': 'bop' != 'bar',\n"
            "}",
            {"foo": "bop", "baz": "qux"},
            matches_matcher,
        ),
        (
            "Extra: {\n  'cat': 'dog',\n}",
            {"foo": "bar", "baz": "quux", "cat": "dog"},
            matches_matcher,
        ),
        (
            "Extra: {\n  'cat': 'dog',\n}\nMissing: {\n  'baz': Not(Equals('qux')),\n}",
            {"foo": "bar", "cat": "dog"},
            matches_matcher,
        ),
    ]


class TestContainsDict(TestCase, TestMatchersInterface):
    matches_matcher: ClassVar = ContainsDict(
        {"foo": Equals("bar"), "baz": Not(Equals("qux"))}
    )

    matches_matches: ClassVar = [
        {"foo": "bar", "baz": None},
        {"foo": "bar", "baz": "quux"},
        {"foo": "bar", "baz": "quux", "cat": "dog"},
    ]
    matches_mismatches: ClassVar = [
        {},
        {"foo": "bar", "baz": "qux"},
        {"foo": "bop", "baz": "qux"},
        {"foo": "bar", "cat": "dog"},
        {"foo": "bar"},
    ]

    str_examples: ClassVar = [
        (
            "ContainsDict({{'baz': {}, 'foo': {}}})".format(
                Not(Equals("qux")), Equals("bar")
            ),
            matches_matcher,
        ),
    ]

    describe_examples: ClassVar = [
        (
            "Missing: {\n  'baz': Not(Equals('qux')),\n  'foo': Equals('bar'),\n}",
            {},
            matches_matcher,
        ),
        (
            "Differences: {\n  'baz': 'qux' matches Equals('qux'),\n}",
            {"foo": "bar", "baz": "qux"},
            matches_matcher,
        ),
        (
            "Differences: {\n"
            "  'baz': 'qux' matches Equals('qux'),\n"
            "  'foo': 'bop' != 'bar',\n"
            "}",
            {"foo": "bop", "baz": "qux"},
            matches_matcher,
        ),
        (
            "Missing: {\n  'baz': Not(Equals('qux')),\n}",
            {"foo": "bar", "cat": "dog"},
            matches_matcher,
        ),
    ]


class TestContainedByDict(TestCase, TestMatchersInterface):
    matches_matcher: ClassVar = ContainedByDict(
        {"foo": Equals("bar"), "baz": Not(Equals("qux"))}
    )

    matches_matches: ClassVar = [
        {},
        {"foo": "bar"},
        {"foo": "bar", "baz": "quux"},
        {"baz": "quux"},
    ]
    matches_mismatches: ClassVar = [
        {"foo": "bar", "baz": "quux", "cat": "dog"},
        {"foo": "bar", "baz": "qux"},
        {"foo": "bop", "baz": "qux"},
        {"foo": "bar", "cat": "dog"},
    ]

    str_examples: ClassVar = [
        (
            "ContainedByDict({{'baz': {}, 'foo': {}}})".format(
                Not(Equals("qux")), Equals("bar")
            ),
            matches_matcher,
        ),
    ]

    describe_examples: ClassVar = [
        (
            "Differences: {\n  'baz': 'qux' matches Equals('qux'),\n}",
            {"foo": "bar", "baz": "qux"},
            matches_matcher,
        ),
        (
            "Differences: {\n"
            "  'baz': 'qux' matches Equals('qux'),\n"
            "  'foo': 'bop' != 'bar',\n"
            "}",
            {"foo": "bop", "baz": "qux"},
            matches_matcher,
        ),
        (
            "Extra: {\n  'cat': 'dog',\n}",
            {"foo": "bar", "cat": "dog"},
            matches_matcher,
        ),
    ]


def test_suite():
    from unittest import TestLoader

    return TestLoader().loadTestsFromName(__name__)
