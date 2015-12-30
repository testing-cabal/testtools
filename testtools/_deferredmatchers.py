# Copyright (c) testtools developers. See LICENSE for details.

"""Matchers that operate on Deferreds.

Depends on Twisted.
"""

from testtools.compat import _u
from testtools.matchers import Mismatch


class _NoResult(object):
    """Matches a Deferred that has not yet fired."""

    def match(self, deferred):
        """Match ``deferred`` if it hasn't fired."""
        result = []

        def callback(x):
            result.append(x)
            # XXX: assertNoResult returns `x` here, but then swallows it if
            # it's a failure. Not 100% sure why that's the case. I guess maybe
            # to handle the case where you assert that there's no result but
            # then later make more assertions / callbacks?
            return x
        deferred.addBoth(callback)
        if result:
            return Mismatch(
                _u('%r has already fired with %r' % (deferred, result[0])))


# XXX: Maybe just a constant, rather than a function?
def no_result():
    """Match a Deferred that has not yet fired."""
    return _NoResult()
