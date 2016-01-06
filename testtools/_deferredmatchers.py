# Copyright (c) testtools developers. See LICENSE for details.

"""Matchers that operate on Deferreds.

Depends on Twisted.
"""

from testtools.compat import _u
from testtools.content import TracebackContent
from testtools.matchers import Mismatch


class _NoResult(object):
    """Matches a Deferred that has not yet fired."""

    def match(self, deferred):
        """Match ``deferred`` if it hasn't fired."""
        result = []

        def callback(x):
            result.append(x)
            # XXX: assertNoResult returns `x` here, but then swallows it if
            # it's a failure. I think this is better behaviour, even if it
            # results in a double traceback.
            return x
        deferred.addBoth(callback)
        if result:
            return Mismatch(
                _u('%r has already fired with %r' % (deferred, result[0])))


# XXX: Maybe just a constant, rather than a function?
def no_result():
    """Match a Deferred that has not yet fired."""
    return _NoResult()


def _not_fired(deferred):
    """Create a mismatch indicating ``deferred`` hasn't fired."""
    return Mismatch(_u('{} has not fired'.format(deferred)))


def _failure_content(failure):
    """Create a Content object for a Failure.

    :param Failure failure: The failure to create content for.
    :rtype: ``Content``
    """
    return TracebackContent(
        (failure.type, failure.value, failure.getTracebackObject()),
        None,
    )


class _Successful(object):
    """Matches a Deferred that has fired successfully."""

    def __init__(self, matcher):
        """Construct a ``_Successful`` matcher."""
        self._matcher = matcher

    def match(self, deferred):
        """Match against the successful result of ``deferred``."""
        successes = []
        failures = []

        def callback(x):
            successes.append(x)
        deferred.addCallbacks(callback, failures.append)

        if successes and failures:
            raise AssertionError(
                _u('Impossible condition, success: {} and failure: {}'.format(
                    successes, failures)))
        elif failures:
            [failure] = failures
            # XXX: attach the traceback
            return Mismatch(
                _u('Success result expected on %r, found failure result '
                   'instead: %r' % (deferred, failure)),
                {'traceback': _failure_content(failure)},
            )
        elif successes:
            [result] = successes
            return self._matcher.match(result)
        else:
            return _not_fired(deferred)


def successful(matcher):
    return _Successful(matcher)


# XXX: Add a convenience for successful(Equals)?
