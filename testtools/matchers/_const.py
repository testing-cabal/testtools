# Copyright (c) 2016 testtools developers. See LICENSE for details.

__all__ = [
    'always',
    'never',
    ]

from testtools.compat import _u
from ._impl import Mismatch


class _Always(object):
    """Always matches."""

    def __str__(self):
        return 'always()'

    def match(self, value):
        return None


def always():
    """
    Always match.

    That is::

        self.assertThat(x, always())

    Will always match and never fail, no matter what ``x`` is. Most useful when
    passed to other higher-order matchers (e.g.
    :py:class:`~testtools.matchers.MatchesListwise`).
    """
    return _Always()


class _Never(object):
    """Never matches."""

    def __str__(self):
        return 'never()'

    def match(self, value):
        return Mismatch(
            _u('Inevitable mismatch on %r' % (value,)))


def never():
    """
    Never match.

    That is::

        self.assertThat(x, never())

    Will never match and always fail, no matter what ``x`` is. Included for
    completeness with :py:func:`.always`, but if you find a use for this, let
    us know!
    """
    return _Never()
