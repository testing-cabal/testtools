# Copyright (c) 2009-2012 testtools developers. See LICENSE for details.

"""Matchers, a way to express complex assertions outside the testcase.

Inspired by 'hamcrest'.

Matcher provides the abstract API that all matchers need to implement.

Bundled matchers are listed in __all__: a list can be obtained by running
$ python -c 'import testtools.matchers; print testtools.matchers.__all__'
"""

__all__ = [
    "Matcher",
    "Mismatch",
    "MismatchDecorator",
    "MismatchError",
]

import unicodedata
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from testtools.testresult import DetailsDict

T = TypeVar("T")


def _slow_escape(text: str) -> str:
    """Escape unicode ``text`` leaving printable characters unmodified

    The behaviour emulates the Python 3 implementation of repr, see
    unicode_repr in unicodeobject.c and isprintable definition.

    Because this iterates over the input a codepoint at a time, it's slow, and
    does not handle astral characters correctly on Python builds with 16 bit
    rather than 32 bit unicode type.
    """
    output: list[str | bytes] = []
    for c in text:
        o = ord(c)
        if o < 256:
            if o < 32 or 126 < o < 161:
                output.append(c.encode("unicode-escape"))
            elif o == 92:
                # Separate due to bug in unicode-escape codec in Python 2.4
                output.append("\\\\")
            else:
                output.append(c)
        else:
            # To get correct behaviour would need to pair up surrogates here
            if unicodedata.category(c)[0] in "CZ":
                output.append(c.encode("unicode-escape"))
            else:
                output.append(c)
    return "".join(output)  # type: ignore[arg-type]


def text_repr(text: str | bytes, multiline: bool | None = None) -> str:
    """Rich repr for ``text`` returning unicode, triple quoted if ``multiline``."""
    nl = (isinstance(text, bytes) and bytes((0xA,))) or "\n"
    if multiline is None:
        multiline = nl in text  # type: ignore[operator]
    if not multiline:
        # Use normal repr for single line of unicode
        return repr(text)
    prefix = repr(text[:0])[:-2]
    if multiline:
        # To escape multiline strings, split and process each line in turn,
        # making sure that quotes are not escaped.
        offset = len(prefix) + 1
        lines = []
        for line in text.split(nl):  # type: ignore[arg-type]
            r = repr(line)
            q = r[-1]
            lines.append(r[offset:-1].replace("\\" + q, q))
        # Combine the escaped lines and append two of the closing quotes,
        # then iterate over the result to escape triple quotes correctly.
        _semi_done = "\n".join(lines) + "''"
        p = 0
        while True:
            p = _semi_done.find("'''", p)
            if p == -1:
                break
            _semi_done = "\\".join([_semi_done[:p], _semi_done[p:]])
            p += 2
        return "".join([prefix, "'''\\\n", _semi_done, "'"])
    escaped_text = _slow_escape(text)
    # Determine which quote character to use and if one gets prefixed with a
    # backslash following the same logic Python uses for repr() on strings
    quote = "'"
    if "'" in text:
        if '"' in text:
            escaped_text = escaped_text.replace("'", "\\'")
        else:
            quote = '"'
    return "".join([prefix, quote, escaped_text, quote])


class Matcher(Generic[T]):
    """A pattern matcher.

    A Matcher must implement match and __str__ to be used by
    testtools.TestCase.assertThat. Matcher.match(thing) returns None when
    thing is completely matched, and a Mismatch object otherwise.

    Matchers can be useful outside of test cases, as they are simply a
    pattern matching language expressed as objects.

    testtools.matchers is inspired by hamcrest, but is pythonic rather than
    a Java transcription.
    """

    def match(self, something: T) -> "Mismatch | None":
        """Return None if this matcher matches something, a Mismatch otherwise."""
        raise NotImplementedError(self.match)

    def __str__(self) -> str:
        """Get a sensible human representation of the matcher.

        This should include the parameters given to the matcher and any
        state that would affect the matches operation.
        """
        raise NotImplementedError(self.__str__)


class Mismatch:
    """An object describing a mismatch detected by a Matcher."""

    def __init__(
        self, description: str | None = None, details: "DetailsDict | None" = None
    ) -> None:
        """Construct a `Mismatch`.

        :param description: A description to use.  If not provided,
            `Mismatch.describe` must be implemented.
        :param details: Extra details about the mismatch.  Defaults
            to the empty dict.
        """
        if description:
            self._description = description
        if details is None:
            details = {}
        self._details = details

    def describe(self) -> str:
        """Describe the mismatch.

        This should be either a human-readable string or castable to a string.
        In particular, is should either be plain ascii or unicode on Python 2,
        and care should be taken to escape control characters.
        """
        try:
            return self._description
        except AttributeError:
            raise NotImplementedError(self.describe)

    def get_details(self) -> "DetailsDict":
        """Get extra details about the mismatch.

        This allows the mismatch to provide extra information beyond the basic
        description, including large text or binary files, or debugging internals
        without having to force it to fit in the output of 'describe'.

        The testtools assertion assertThat will query get_details and attach
        all its values to the test, permitting them to be reported in whatever
        manner the test environment chooses.

        :return: a dict mapping names to Content objects. name is a string to
            name the detail, and the Content object is the detail to add
            to the result. For more information see the API to which items from
            this dict are passed testtools.TestCase.addDetail.
        """
        return getattr(self, "_details", {})

    def __repr__(self) -> str:
        return (
            f"<testtools.matchers.Mismatch object at {id(self):x} "
            f"attributes={self.__dict__!r}>"
        )


class MismatchError(AssertionError, Generic[T]):
    """Raised when a mismatch occurs."""

    # This class exists to work around
    # <https://bugs.launchpad.net/testtools/+bug/804127>.  It provides a
    # guaranteed way of getting a readable exception, no matter what crazy
    # characters are in the matchee, matcher or mismatch.

    def __init__(
        self, matchee: T, matcher: Matcher[T], mismatch: Mismatch, verbose: bool = False
    ) -> None:
        super().__init__()
        self.matchee = matchee
        self.matcher = matcher
        self.mismatch = mismatch
        self.verbose = verbose

    def __str__(self) -> str:
        difference = self.mismatch.describe()
        if self.verbose:
            # GZ 2011-08-24: Smelly API? Better to take any object and special
            #                case text inside?
            if isinstance(self.matchee, (str, bytes)):
                matchee = text_repr(self.matchee, multiline=False)
            else:
                matchee = repr(self.matchee)
            return (
                f"Match failed. Matchee: {matchee}\n"
                f"Matcher: {self.matcher}\nDifference: {difference}\n"
            )
        else:
            return difference


class MismatchDecorator(Mismatch):
    """Decorate a ``Mismatch``.

    Forwards all messages to the original mismatch object.  Probably the best
    way to use this is inherit from this class and then provide your own
    custom decoration logic.
    """

    def __init__(self, original: Mismatch) -> None:
        """Construct a `MismatchDecorator`.

        :param original: A `Mismatch` object to decorate.
        """
        self.original = original

    def __repr__(self) -> str:
        return f"<testtools.matchers.MismatchDecorator({self.original!r})>"

    def describe(self) -> str:
        return self.original.describe()

    def get_details(self) -> "DetailsDict":
        return self.original.get_details()


# Signal that this is part of the testing framework, and that code from this
# should not normally appear in tracebacks.
__unittest = True
