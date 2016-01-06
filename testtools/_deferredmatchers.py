# Copyright (c) testtools developers. See LICENSE for details.

"""Matchers that operate on Deferreds.

Depends on Twisted.
"""

# XXX: None of these are published yet. Decide where & how to make them public.

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
    # TODO: Example in docstrings
    return _NoResult()


def _not_fired(deferred):
    """Create a mismatch indicating ``deferred`` hasn't fired."""
    # XXX: Make sure that the error messages we generate are the same as the
    # error messages that Twisted returns.
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


# XXX: The Twisted name is successResultOf. Do we want to use that name?
def successful(matcher):
    # XXX: Docstring, include examples.
    return _Successful(matcher)


# XXX: Add a convenience for successful(Equals)?

class _Failed(object):
    """Matches a Deferred that has failed."""

    def __init__(self, matcher):
        self._matcher = matcher

    def match(self, deferred):
        successes = []
        failures = []
        deferred.addCallbacks(successes.append, failures.append)
        # XXX: This duplicates structure (oh for pattern matching!). Can I do
        # some sort of OO trickery to avoid this?
        if successes and failures:
            raise AssertionError(
                _u('Impossible condition, success: {} and failure: {}'.format(
                    successes, failures)))
        elif failures:
            [failure] = failures
            return self._matcher.match(failure)
        elif successes:
            [success] = successes
            return Mismatch(
                _u('Failure result expected on %r, found success '
                   'result (%r) instead' % (deferred, success)), {})
        else:
            return Mismatch(
                _u('Failure result expected on %r, found no result instead'
                   % (deferred,)))


# XXX: The Twisted name is failureResultOf. Do we want to use that name?
#
# XXX: failureResultOf also takes an *args of expected exception types. Do we
# want to provide that?
def failed(matcher):
    # XXX: Docstring, with examples.
    return _Failed(matcher)

# TODO: helpers for adding matcher-based assertions in callbacks.
