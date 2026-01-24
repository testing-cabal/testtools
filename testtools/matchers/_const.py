# Copyright (c) 2016 testtools developers. See LICENSE for details.

__all__ = [
    "Always",
    "Never",
]


from ._impl import Matcher, Mismatch


class _Always(Matcher[object]):
    """Always matches."""

    def __str__(self) -> str:
        return "Always()"

    def match(self, value: object) -> None:
        return None


def Always() -> _Always:
    """Always match.

    That is::

        self.assertThat(x, Always())

    Will always match and never fail, no matter what ``x`` is. Most useful when
    passed to other higher-order matchers (e.g.
    :py:class:`~testtools.matchers.MatchesListwise`).
    """
    return _Always()


class _Never(Matcher[object]):
    """Never matches."""

    def __str__(self) -> str:
        return "Never()"

    def match(self, value: object) -> Mismatch:
        return Mismatch(f"Inevitable mismatch on {value!r}")


def Never() -> _Never:
    """Never match.

    That is::

        self.assertThat(x, Never())

    Will never match and always fail, no matter what ``x`` is. Included for
    completeness with :py:func:`.Always`, but if you find a use for this, let
    us know!
    """
    return _Never()
