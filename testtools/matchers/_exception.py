# Copyright (c) 2009-2012 testtools developers. See LICENSE for details.

__all__ = [
    "MatchesException",
    "Raises",
    "raises",
]

import sys
import types
from collections.abc import Callable
from typing import TypeAlias, TypeVar

from ._basic import MatchesRegex
from ._higherorder import AfterPreprocessing
from ._impl import Matcher, Mismatch

# Type for exc_info tuples
ExcInfo: TypeAlias = tuple[
    type[BaseException], BaseException, types.TracebackType | None
]

T = TypeVar("T", bound=BaseException)

_error_repr = BaseException.__repr__


def _is_exception(exc: object) -> bool:
    return isinstance(exc, BaseException)


def _is_user_exception(exc: object) -> bool:
    return isinstance(exc, Exception)


class MatchesException(Matcher[ExcInfo]):
    """Match an exc_info tuple against an exception instance or type."""

    def __init__(
        self,
        exception: BaseException
        | type[BaseException]
        | tuple[type[BaseException], ...],
        value_re: "str | Matcher[BaseException] | None" = None,
    ) -> None:
        """Create a MatchesException that will match exc_info's for exception.

        :param exception: Either an exception instance or type.
            If an instance is given, the type and arguments of the exception
            are checked. If a type is given only the type of the exception is
            checked. If a tuple is given, then as with isinstance, any of the
            types in the tuple matching is sufficient to match.
        :param value_re: If 'exception' is a type, and the matchee exception
            is of the right type, then match against this.  If value_re is a
            string, then assume value_re is a regular expression and match
            the str() of the exception against it.  Otherwise, assume value_re
            is a matcher, and match the exception against it.
        """
        Matcher.__init__(self)
        self.expected = exception
        value_matcher: Matcher[BaseException] | None
        if isinstance(value_re, str):
            value_matcher = AfterPreprocessing(str, MatchesRegex(value_re), False)
        else:
            value_matcher = value_re
        self.value_re = value_matcher
        expected_type = type(self.expected)
        self._is_instance = not any(
            issubclass(expected_type, class_type) for class_type in (type, tuple)
        )

    def match(self, other: ExcInfo) -> Mismatch | None:
        if not isinstance(other, tuple):
            return Mismatch(f"{other!r} is not an exc_info tuple")
        expected_class: type[BaseException]
        if self._is_instance:
            assert isinstance(self.expected, BaseException)
            expected_class = self.expected.__class__
        else:
            if isinstance(self.expected, tuple):
                # For tuple of types, just use the first one for error message
                expected_class = self.expected[0]
            else:
                assert isinstance(self.expected, type)
                expected_class = self.expected

        # Check if other[0] is a subclass of expected_class
        exc_type = other[0]
        if isinstance(self.expected, tuple):
            if not any(issubclass(exc_type, cls) for cls in self.expected):
                return Mismatch(f"{exc_type!r} is not a {self.expected!r}")
        else:
            if not issubclass(exc_type, expected_class):
                return Mismatch(f"{exc_type!r} is not a {expected_class!r}")

        if self._is_instance:
            assert isinstance(self.expected, BaseException)
            if other[1].args != self.expected.args:
                return Mismatch(
                    f"{_error_repr(other[1])} has different arguments to "
                    f"{_error_repr(self.expected)}."
                )
        elif self.value_re is not None:
            return self.value_re.match(other[1])
        return None

    def __str__(self) -> str:
        if self._is_instance:
            assert isinstance(self.expected, BaseException)
            return f"MatchesException({_error_repr(self.expected)})"
        return f"MatchesException({self.expected!r})"


class Raises(Matcher[Callable[[], object]]):
    """Match if the matchee raises an exception when called.

    Exceptions which are not subclasses of Exception propagate out of the
    Raises.match call unless they are explicitly matched.
    """

    def __init__(self, exception_matcher: "Matcher[ExcInfo] | None" = None) -> None:
        """Create a Raises matcher.

        :param exception_matcher: Optional validator for the exception raised
            by matchee. If supplied the exc_info tuple for the exception raised
            is passed into that matcher. If no exception_matcher is supplied
            then the simple fact of raising an exception is considered enough
            to match on.
        """
        self.exception_matcher = exception_matcher

    def match(self, matchee: "Callable[[], object]") -> Mismatch | None:
        try:
            # Handle staticmethod objects by extracting the underlying function
            actual_callable: Callable[[], object]
            if isinstance(matchee, staticmethod):
                actual_callable = matchee.__func__  # type: ignore[assignment]
            else:
                actual_callable = matchee
            result = actual_callable()
            return Mismatch(f"{matchee!r} returned {result!r}")
        # Catch all exceptions: Raises() should be able to match a
        # KeyboardInterrupt or SystemExit.
        except BaseException:
            exc_info = sys.exc_info()
            # Type narrow to actual ExcInfo
            assert exc_info[0] is not None
            assert exc_info[1] is not None
            typed_exc_info: ExcInfo = (exc_info[0], exc_info[1], exc_info[2])  # type: ignore[assignment]

            if self.exception_matcher:
                mismatch = self.exception_matcher.match(typed_exc_info)
                if not mismatch:
                    del exc_info
                    return None
            else:
                mismatch = None
            # The exception did not match, or no explicit matching logic was
            # performed. If the exception is a non-user exception then
            # propagate it.
            exception = typed_exc_info[1]
            if _is_exception(exception) and not _is_user_exception(exception):
                del exc_info
                raise
            return mismatch

    def __str__(self) -> str:
        return "Raises()"


def raises(
    exception: BaseException | type[BaseException] | tuple[type[BaseException], ...],
) -> Raises:
    """Make a matcher that checks that a callable raises an exception.

    This is a convenience function, exactly equivalent to::

        return Raises(MatchesException(exception))

    See `Raises` and `MatchesException` for more information.
    """
    return Raises(MatchesException(exception))
