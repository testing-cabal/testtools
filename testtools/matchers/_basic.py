# Copyright (c) 2009-2012 testtools developers. See LICENSE for details.

__all__ = [
    "Contains",
    "EndsWith",
    "Equals",
    "GreaterThan",
    "HasLength",
    "Is",
    "IsInstance",
    "LessThan",
    "MatchesRegex",
    "Nearly",
    "NotEquals",
    "SameMembers",
    "StartsWith",
]

import operator
import re
from collections.abc import Callable
from pprint import pformat
from typing import Any, Generic, TypeVar

from ..compat import (
    text_repr,
)
from ..helpers import list_subtract
from ._higherorder import (
    MatchesPredicateWithParams,
    PostfixedMismatch,
)
from ._impl import (
    Matcher,
    Mismatch,
)

T = TypeVar("T")
U = TypeVar("U")


def _format(thing: object) -> str:
    """Blocks of text with newlines are formatted as triple-quote
    strings. Everything else is pretty-printed.
    """
    if isinstance(thing, (str, bytes)):
        result: str = text_repr(thing)
        return result
    pformat_result: str = pformat(thing)
    return pformat_result


class _BinaryComparison(Matcher[T]):
    """Matcher that compares an object to another object."""

    mismatch_string: str
    # comparator is defined by subclasses - using Any to allow different signatures
    comparator: Callable[..., Any]

    def __init__(self, expected: T) -> None:
        self.expected = expected

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.expected!r})"

    def match(self, other: T) -> Mismatch | None:
        if self.comparator(other, self.expected):
            return None
        return _BinaryMismatch(other, self.mismatch_string, self.expected)


class _BinaryMismatch(Mismatch, Generic[T]):
    """Two things did not match."""

    def __init__(
        self,
        actual: T,
        mismatch_string: str,
        reference: T,
        reference_on_right: bool = True,
    ) -> None:
        self._actual = actual
        self._mismatch_string = mismatch_string
        self._reference = reference
        self._reference_on_right = reference_on_right

    def describe(self) -> str:
        # Special handling for set comparisons
        if (
            self._mismatch_string == "!="
            and isinstance(self._reference, set)
            and isinstance(self._actual, set)
        ):
            result: str = self._describe_set_difference()
            return result

        actual = repr(self._actual)
        reference = repr(self._reference)
        if len(actual) + len(reference) > 70:
            return (
                f"{self._mismatch_string}:\n"
                f"reference = {_format(self._reference)}\n"
                f"actual    = {_format(self._actual)}\n"
            )
        else:
            if self._reference_on_right:
                left, right = actual, reference
            else:
                left, right = reference, actual
            return f"{left} {self._mismatch_string} {right}"

    def _describe_set_difference(self) -> str:
        """Describe the difference between two sets in a readable format."""
        # Type narrowing: we know these are sets from the isinstance check in describe()
        assert isinstance(self._reference, set)
        assert isinstance(self._actual, set)

        reference_only = sorted(
            self._reference - self._actual, key=lambda x: (type(x).__name__, x)
        )
        actual_only = sorted(
            self._actual - self._reference, key=lambda x: (type(x).__name__, x)
        )

        lines = ["!=:"]
        if reference_only:
            lines.append(
                f"Items in expected but not in actual:\n{_format(reference_only)}"
            )
        if actual_only:
            lines.append(
                f"Items in actual but not in expected:\n{_format(actual_only)}"
            )

        return "\n".join(lines)


class Equals(_BinaryComparison[T]):
    """Matches if the items are equal."""

    comparator = operator.eq
    mismatch_string = "!="


class _FlippedEquals(Matcher[T]):
    """Matches if the items are equal.

    Exactly like ``Equals`` except that the short mismatch message is "
    $reference != $actual" rather than "$actual != $reference". This allows
    for ``TestCase.assertEqual`` to use a matcher but still have the order of
    items in the error message align with the order of items in the call to
    the assertion.
    """

    def __init__(self, expected: T) -> None:
        self._expected = expected

    def __str__(self) -> str:
        return f"_FlippedEquals({self._expected!r})"

    def match(self, other: T) -> Mismatch | None:
        mismatch = Equals(self._expected).match(other)
        if not mismatch:
            return None
        return _BinaryMismatch(other, "!=", self._expected, False)


class NotEquals(_BinaryComparison[T]):
    """Matches if the items are not equal.

    In most cases, this is equivalent to ``Not(Equals(foo))``. The difference
    only matters when testing ``__ne__`` implementations.
    """

    comparator = operator.ne
    mismatch_string = "=="


class Is(_BinaryComparison[T]):
    """Matches if the items are identical."""

    comparator = operator.is_
    mismatch_string = "is not"


class LessThan(_BinaryComparison[T]):
    """Matches if the item is less than the matchers reference object."""

    comparator = operator.lt
    mismatch_string = ">="


class GreaterThan(_BinaryComparison[T]):
    """Matches if the item is greater than the matchers reference object."""

    comparator = operator.gt
    mismatch_string = "<="


class _NotNearlyEqual(Mismatch, Generic[T]):
    """Mismatch for Nearly matcher."""

    def __init__(self, actual: T, expected: T, delta: Any) -> None:
        self.actual = actual
        self.expected = expected
        self.delta = delta

    def describe(self) -> str:
        try:
            diff = abs(self.actual - self.expected)  # type: ignore[operator]
            return (
                f"{self.actual!r} is not nearly equal to {self.expected!r}: "
                f"difference {diff!r} exceeds tolerance {self.delta!r}"
            )
        except (TypeError, AttributeError):
            return (
                f"{self.actual!r} is not nearly equal to {self.expected!r} "
                f"within {self.delta!r}"
            )


class Nearly(Matcher[T]):
    """Matches if a value is nearly equal to the expected value.

    This matcher is useful for comparing floating point values where exact
    equality cannot be relied upon due to precision limitations.

    The matcher checks if the absolute difference between the actual and
    expected values is less than or equal to a specified tolerance (delta).

    This works for any type that supports subtraction and absolute value
    operations (e.g., integers, floats, Decimal, etc.).
    """

    def __init__(self, expected: T, delta: Any = 0.001) -> None:
        """Create a Nearly matcher.

        :param expected: The expected value to compare against.
        :param delta: The maximum allowed absolute difference (tolerance).
            Default is 0.001.
        """
        self.expected = expected
        self.delta = delta

    def __str__(self) -> str:
        return f"Nearly({self.expected!r}, delta={self.delta!r})"

    def match(self, actual: T) -> Mismatch | None:
        try:
            diff = abs(actual - self.expected)  # type: ignore[operator]
            if diff <= self.delta:
                return None
        except (TypeError, AttributeError):
            # Can't compute difference - definitely not nearly equal
            pass
        return _NotNearlyEqual(actual, self.expected, self.delta)


class SameMembers(Matcher[list[T]]):
    """Matches if two iterators have the same members.

    This is not the same as set equivalence.  The two iterators must be of the
    same length and have the same repetitions.
    """

    def __init__(self, expected: list[T]) -> None:
        super().__init__()
        self.expected = expected

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.expected!r})"

    def match(self, observed: list[T]) -> Mismatch | None:
        expected_only = list_subtract(self.expected, observed)
        observed_only = list_subtract(observed, self.expected)
        if expected_only == observed_only == []:
            return None
        return PostfixedMismatch(
            (
                f"\nmissing:    {_format(expected_only)}\n"
                f"extra:      {_format(observed_only)}"
            ),
            _BinaryMismatch(observed, "elements differ", self.expected),
        )


class DoesNotStartWith(Mismatch):
    def __init__(self, matchee: str | bytes, expected: str | bytes) -> None:
        """Create a DoesNotStartWith Mismatch.

        :param matchee: the string that did not match.
        :param expected: the string that 'matchee' was expected to start with.
        """
        self.matchee = matchee
        self.expected = expected

    def describe(self) -> str:
        return (
            f"{text_repr(self.matchee)} does not start with {text_repr(self.expected)}."
        )


class StartsWith(Matcher[str | bytes]):
    """Checks whether one string starts with another."""

    def __init__(self, expected: str | bytes) -> None:
        """Create a StartsWith Matcher.

        :param expected: the string that matchees should start with.
        """
        self.expected = expected

    def __str__(self) -> str:
        return f"StartsWith({self.expected!r})"

    def match(self, matchee: str | bytes) -> Mismatch | None:
        if not matchee.startswith(self.expected):  # type: ignore[arg-type]
            return DoesNotStartWith(matchee, self.expected)
        return None


class DoesNotEndWith(Mismatch):
    def __init__(self, matchee: str | bytes, expected: str | bytes) -> None:
        """Create a DoesNotEndWith Mismatch.

        :param matchee: the string that did not match.
        :param expected: the string that 'matchee' was expected to end with.
        """
        self.matchee = matchee
        self.expected = expected

    def describe(self) -> str:
        return (
            f"{text_repr(self.matchee)} does not end with {text_repr(self.expected)}."
        )


class EndsWith(Matcher[str | bytes]):
    """Checks whether one string ends with another."""

    def __init__(self, expected: str | bytes) -> None:
        """Create a EndsWith Matcher.

        :param expected: the string that matchees should end with.
        """
        self.expected = expected

    def __str__(self) -> str:
        return f"EndsWith({self.expected!r})"

    def match(self, matchee: str | bytes) -> Mismatch | None:
        if not matchee.endswith(self.expected):  # type: ignore[arg-type]
            return DoesNotEndWith(matchee, self.expected)
        return None


class IsInstance(Matcher[T]):
    """Matcher that wraps isinstance."""

    def __init__(self, *types: type[T]) -> None:
        self.types = tuple(types)

    def __str__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__, ", ".join(type.__name__ for type in self.types)
        )

    def match(self, other: T) -> Mismatch | None:
        if isinstance(other, self.types):
            return None
        return NotAnInstance(other, self.types)


class NotAnInstance(Mismatch, Generic[T]):
    def __init__(self, matchee: T, types: tuple[type[T], ...]) -> None:
        """Create a NotAnInstance Mismatch.

        :param matchee: the thing which is not an instance of any of types.
        :param types: A tuple of the types which were expected.
        """
        self.matchee = matchee
        self.types = types

    def describe(self) -> str:
        if len(self.types) == 1:
            typestr = self.types[0].__name__
        else:
            typestr = "any of ({})".format(
                ", ".join(type.__name__ for type in self.types)
            )
        return f"'{self.matchee}' is not an instance of {typestr}"


class DoesNotContain(Mismatch, Generic[T, U]):
    def __init__(self, matchee: T, needle: U) -> None:
        """Create a DoesNotContain Mismatch.

        :param matchee: the object that did not contain needle.
        :param needle: the needle that 'matchee' was expected to contain.
        """
        self.matchee = matchee
        self.needle = needle

    def describe(self) -> str:
        return f"{self.needle!r} not in {self.matchee!r}"


class Contains(Matcher[T], Generic[T, U]):
    """Checks whether something is contained in another thing."""

    def __init__(self, needle: U) -> None:
        """Create a Contains Matcher.

        :param needle: the thing that needs to be contained by matchees.
        """
        self.needle = needle

    def __str__(self) -> str:
        return f"Contains({self.needle!r})"

    def match(self, matchee: T) -> Mismatch | None:
        try:
            if self.needle not in matchee:  # type: ignore[operator]
                return DoesNotContain(matchee, self.needle)
        except TypeError:
            # e.g. 1 in 2 will raise TypeError
            return DoesNotContain(matchee, self.needle)
        return None


class MatchesRegex(Matcher[str]):
    """Matches if the matchee is matched by a regular expression."""

    def __init__(self, pattern: str | bytes, flags: int = 0) -> None:
        self.pattern = pattern
        self.flags = flags

    def __str__(self) -> str:
        args = [f"{self.pattern!r}"]
        flag_arg = []
        # dir() sorts the attributes for us, so we don't need to do it again.
        for flag in dir(re):
            if len(flag) == 1:
                if self.flags & getattr(re, flag):
                    flag_arg.append(f"re.{flag}")
        if flag_arg:
            args.append("|".join(flag_arg))
        return "{}({})".format(self.__class__.__name__, ", ".join(args))

    def match(self, value: str) -> Mismatch | None:
        if not re.match(self.pattern, value, self.flags):  # type: ignore[arg-type]
            pattern = self.pattern
            if not isinstance(pattern, str):
                pattern = pattern.decode("latin1")
            pattern = pattern.encode("unicode_escape").decode("ascii")
            return Mismatch(
                "{!r} does not match /{}/".format(value, pattern.replace("\\\\", "\\"))
            )
        return None


def has_len(x: Any, y: int) -> bool:
    return len(x) == y


HasLength = MatchesPredicateWithParams(has_len, "len({0}) != {1}", "HasLength")
