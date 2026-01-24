# Copyright (c) 2009-2012 testtools developers. See LICENSE for details.

__all__ = [
    "KeysEqual",
]

from collections.abc import Callable
from typing import Any, ClassVar, Generic, TypeVar

from ..helpers import (
    dict_subtract,
    filter_values,
    map_values,
)
from ._higherorder import (
    AnnotatedMismatch,
    MismatchesAll,
    PrefixedMismatch,
)
from ._impl import Matcher, Mismatch

K = TypeVar("K")
V = TypeVar("V")


def LabelledMismatches(
    mismatches: dict[Any, Mismatch], details: Any = None
) -> MismatchesAll:
    """A collection of mismatches, each labelled."""
    return MismatchesAll(
        (PrefixedMismatch(k, v) for (k, v) in sorted(mismatches.items())), wrap=False
    )


class MatchesAllDict(Matcher[Any]):
    """Matches if all of the matchers it is created with match.

    A lot like ``MatchesAll``, but takes a dict of Matchers and labels any
    mismatches with the key of the dictionary.
    """

    def __init__(self, matchers: dict[Any, "Matcher[Any]"]) -> None:
        super().__init__()
        self.matchers = matchers

    def __str__(self) -> str:
        return f"MatchesAllDict({_format_matcher_dict(self.matchers)})"

    def match(self, observed: Any) -> Mismatch | None:
        mismatches: dict[Any, Mismatch | None] = {}
        for label in self.matchers:
            mismatches[label] = self.matchers[label].match(observed)
        return _dict_to_mismatch(mismatches, result_mismatch=LabelledMismatches)


class DictMismatches(Mismatch):
    """A mismatch with a dict of child mismatches."""

    def __init__(self, mismatches: dict[Any, Mismatch], details: Any = None) -> None:
        super().__init__(None, details=details)
        self.mismatches = mismatches

    def describe(self) -> str:
        lines = ["{"]
        lines.extend(
            [
                f"  {key!r}: {mismatch.describe()},"
                for (key, mismatch) in sorted(self.mismatches.items())
            ]
        )
        lines.append("}")
        return "\n".join(lines)


def _dict_to_mismatch(
    data: dict[K, V | None],
    to_mismatch: "Callable[[V], Mismatch] | None" = None,
    result_mismatch: "Callable[[dict[K, Mismatch]], Mismatch]" = DictMismatches,
) -> Mismatch | None:
    if to_mismatch:
        data = map_values(to_mismatch, data)  # type: ignore[arg-type,assignment]
    mismatches = filter_values(bool, data)  # type: ignore[arg-type]
    if mismatches:
        return result_mismatch(mismatches)  # type: ignore[arg-type]
    return None


class _MatchCommonKeys(Matcher[dict[Any, Any]]):
    """Match on keys in a dictionary.

    Given a dictionary where the values are matchers, this will look for
    common keys in the matched dictionary and match if and only if all common
    keys match the given matchers.

    Thus::

      >>> structure = {'a': Equals('x'), 'b': Equals('y')}
      >>> _MatchCommonKeys(structure).match({'a': 'x', 'c': 'z'})
      None
    """

    def __init__(self, dict_of_matchers: dict[Any, "Matcher[Any]"]) -> None:
        super().__init__()
        self._matchers = dict_of_matchers

    def _compare_dicts(
        self, expected: dict[Any, "Matcher[Any]"], observed: dict[Any, Any]
    ) -> dict[Any, Mismatch]:
        common_keys = set(expected.keys()) & set(observed.keys())
        mismatches: dict[Any, Mismatch] = {}
        for key in common_keys:
            mismatch = expected[key].match(observed[key])
            if mismatch:
                mismatches[key] = mismatch
        return mismatches

    def match(self, observed: dict[Any, Any]) -> Mismatch | None:
        mismatches = self._compare_dicts(self._matchers, observed)
        if mismatches:
            return DictMismatches(mismatches)
        return None


class _SubDictOf(Matcher[dict[Any, Any]]):
    """Matches if the matched dict only has keys that are in given dict."""

    def __init__(
        self, super_dict: dict[Any, Any], format_value: Callable[[Any], str] = repr
    ) -> None:
        super().__init__()
        self.super_dict = super_dict
        self.format_value = format_value

    def match(self, observed: dict[Any, Any]) -> Mismatch | None:
        excess = dict_subtract(observed, self.super_dict)
        return _dict_to_mismatch(excess, lambda v: Mismatch(self.format_value(v)))


class _SuperDictOf(Matcher[dict[Any, Any]]):
    """Matches if all of the keys in the given dict are in the matched dict."""

    def __init__(
        self, sub_dict: dict[Any, Any], format_value: Callable[[Any], str] = repr
    ) -> None:
        super().__init__()
        self.sub_dict = sub_dict
        self.format_value = format_value

    def match(self, super_dict: dict[Any, Any]) -> Mismatch | None:
        return _SubDictOf(super_dict, self.format_value).match(self.sub_dict)


def _format_matcher_dict(matchers: dict[str, "Matcher[Any]"]) -> str:
    return "{{{}}}".format(
        ", ".join(sorted(f"{k!r}: {v}" for k, v in matchers.items()))
    )


class _CombinedMatcher(Matcher[dict[Any, Any]]):
    """Many matchers labelled and combined into one uber-matcher.

    Subclass this and then specify a dict of matcher factories that take a
    single 'expected' value and return a matcher.  The subclass will match
    only if all of the matchers made from factories match.

    Not **entirely** dissimilar from ``MatchesAll``.
    """

    matcher_factories: ClassVar[dict[str, Any]] = {}

    def __init__(self, expected: dict[str, "Matcher[Any]"]) -> None:
        super().__init__()
        self._expected = expected

    def format_expected(self, expected: dict[str, "Matcher[Any]"]) -> str:
        return repr(expected)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.format_expected(self._expected)})"

    def match(self, observed: dict[Any, Any]) -> Mismatch | None:
        matchers = {k: v(self._expected) for k, v in self.matcher_factories.items()}
        return MatchesAllDict(matchers).match(observed)


class MatchesDict(_CombinedMatcher):
    """Match a dictionary exactly, by its keys.

    Specify a dictionary mapping keys (often strings) to matchers.  This is
    the 'expected' dict.  Any dictionary that matches this must have exactly
    the same keys, and the values must match the corresponding matchers in the
    expected dict.
    """

    matcher_factories: ClassVar[dict[str, Any]] = {
        "Extra": _SubDictOf,
        "Missing": lambda m: _SuperDictOf(m, format_value=str),
        "Differences": _MatchCommonKeys,
    }

    def format_expected(self, expected: dict[str, "Matcher[Any]"]) -> str:
        return _format_matcher_dict(expected)


class ContainsDict(_CombinedMatcher):
    """Match a dictionary for that contains a specified sub-dictionary.

    Specify a dictionary mapping keys (often strings) to matchers.  This is
    the 'expected' dict.  Any dictionary that matches this must have **at
    least** these keys, and the values must match the corresponding matchers
    in the expected dict.  Dictionaries that have more keys will also match.

    In other words, any matching dictionary must contain the dictionary given
    to the constructor.

    Does not check for strict sub-dictionary.  That is, equal dictionaries
    match.
    """

    matcher_factories: ClassVar[dict[str, Any]] = {
        "Missing": lambda m: _SuperDictOf(m, format_value=str),
        "Differences": _MatchCommonKeys,
    }

    def format_expected(self, expected: dict[str, "Matcher[Any]"]) -> str:
        return _format_matcher_dict(expected)


class ContainedByDict(_CombinedMatcher):
    """Match a dictionary for which this is a super-dictionary.

    Specify a dictionary mapping keys (often strings) to matchers.  This is
    the 'expected' dict.  Any dictionary that matches this must have **only**
    these keys, and the values must match the corresponding matchers in the
    expected dict.  Dictionaries that have fewer keys can also match.

    In other words, any matching dictionary must be contained by the
    dictionary given to the constructor.

    Does not check for strict super-dictionary.  That is, equal dictionaries
    match.
    """

    matcher_factories: ClassVar[dict[str, Any]] = {
        "Extra": _SubDictOf,
        "Differences": _MatchCommonKeys,
    }

    def format_expected(self, expected: dict[str, "Matcher[Any]"]) -> str:
        return _format_matcher_dict(expected)


class KeysEqual(Matcher[dict[K, Any]], Generic[K]):
    """Checks whether a dict has particular keys."""

    def __init__(self, *expected: K) -> None:
        """Create a `KeysEqual` Matcher.

        :param expected: The keys the matchee is expected to have. As a
            special case, if a single argument is specified, and it is a
            mapping, then we use its keys as the expected set.
        """
        super().__init__()
        expected_keys: tuple[K, ...] | Any = expected
        if len(expected) == 1:
            try:
                expected_keys = expected[0].keys()  # type: ignore[attr-defined]
            except AttributeError:
                pass
        self.expected: list[K] = list(expected_keys)

    def __str__(self) -> str:
        return "KeysEqual({})".format(", ".join(map(repr, self.expected)))

    def match(self, matchee: dict[K, Any]) -> Mismatch | None:
        from ._basic import Equals, _BinaryMismatch

        expected = sorted(self.expected)  # type: ignore[type-var]
        matched = Equals(expected).match(sorted(matchee.keys()))  # type: ignore[type-var]
        if matched:
            return AnnotatedMismatch(
                "Keys not equal", _BinaryMismatch(expected, "does not match", matchee)
            )
        return None
