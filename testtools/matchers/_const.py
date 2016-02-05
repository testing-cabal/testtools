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
    """Always match."""
    return _Always()


class _Never(object):
    """Never matches."""

    def __str__(self):
        return 'never()'

    def match(self, value):
        return Mismatch(
            _u('Inevitable mismatch on %r' % (value,)))


def never():
    """Never match."""
    return _Never()
