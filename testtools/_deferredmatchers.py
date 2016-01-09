# Copyright (c) testtools developers. See LICENSE for details.

"""Matchers that operate on Deferreds.

Depends on Twisted.
"""

# TODO: None of these are published yet. Decide where & how to make them
# public.
from functools import partial

from testtools.compat import _u
from testtools.content import TracebackContent
from testtools.matchers import Mismatch


class ImpossibleDeferredError(Exception):
    """
    Raised if a Deferred somehow triggers both a success and a failure.
    """

    def __init__(self, deferred, successes, failures):
        super(ImpossibleDeferredError, self).__init__(
            'Impossible condition on {}, got both success ({}) and '
            'failure ({})'.format(deferred, successes, failures)
        )


def _on_deferred_result(deferred, on_success, on_failure, on_no_result):
    """Handle the result of a synchronous ``Deferred``.

    If ``deferred`` has fire successfully, call ``on_success``.
    If ``deferred`` has failed, call ``on_failure``.
    If ``deferred`` has not yet fired, call ``on_no_result``.

    The value of ``deferred`` will be preserved, so that other callbacks and
    errbacks can be added to ``deferred``.

    :param Deferred deferred: A synchronous Deferred.
    :param Callable[[Any], T] on_success: Called if the Deferred fires
        successfully.
    :param Callable[[Failure], T] on_failure: Called if the Deferred
        fires unsuccessfully.
    :param Callable[[], T] on_no_result: Called if the Deferred has not
        yet fired.

    :raises ImpossibleDeferredError: If the Deferred somehow
        triggers both a success and a failure.
    :raises TypeError: If the Deferred somehow triggers more than one success,
        or more than one failure.

    :return: Whatever is returned by the triggered callback.
    :rtype: ``T``
    """
    # XXX: I desperately want to decompose this into an Either and a Maybe,
    # and a thing that returns Maybe (Either Failure a) given a synchronous
    # Deferred. I am restraining myself.
    successes = []
    failures = []

    def capture(value, values):
        values.append(value)
        return value

    deferred.addCallbacks(
        partial(capture, values=successes),
        partial(capture, values=failures),
    )

    if successes and failures:
        raise ImpossibleDeferredError(deferred, successes, failures)
    elif failures:
        [failure] = failures
        return on_failure(failure)
    elif successes:
        [result] = successes
        return on_success(result)
    else:
        return on_no_result()


class _NoResult(object):
    """Matches a Deferred that has not yet fired."""

    @staticmethod
    def _got_result(deferred, result):
        return Mismatch(
            _u('No result expected on %r, found %r instead'
               % (deferred, result)))

    def match(self, deferred):
        """Match ``deferred`` if it hasn't fired."""
        return _on_deferred_result(
            deferred,
            on_success=partial(self._got_result, deferred),
            on_failure=partial(self._got_result, deferred),
            on_no_result=lambda: None,
        )


# XXX: Maybe just a constant, rather than a function?
def no_result():
    """Match a Deferred that has not yet fired."""
    # TODO: Example in docstrings
    return _NoResult()


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

    @staticmethod
    def _got_failure(deferred, failure):
        deferred.addErrback(lambda _: None)
        return Mismatch(
            _u('Success result expected on %r, found failure result '
               'instead: %r' % (deferred, failure)),
            {'traceback': _failure_content(failure)},
        )

    @staticmethod
    def _got_no_result(deferred):
        return Mismatch(
            _u('Success result expected on {}, found no result '
               'instead'.format(deferred)))

    def match(self, deferred):
        """Match against the successful result of ``deferred``."""
        return _on_deferred_result(
            deferred,
            on_success=self._matcher.match,
            on_failure=partial(self._got_failure, deferred),
            on_no_result=partial(self._got_no_result, deferred),
        )


# XXX: The Twisted name is successResultOf. Do we want to use that name?
def successful(matcher):
    # XXX: Docstring, include examples.
    return _Successful(matcher)


# XXX: Add a convenience for successful(Equals)?

class _Failed(object):
    """Matches a Deferred that has failed."""

    def __init__(self, matcher):
        self._matcher = matcher

    def _got_failure(self, deferred, failure):
        # We have handled the failure, so suppress its output.
        deferred.addErrback(lambda _: None)
        return self._matcher.match(failure)

    @staticmethod
    def _got_success(deferred, success):
        return Mismatch(
            _u('Failure result expected on %r, found success '
               'result (%r) instead' % (deferred, success)), {})

    @staticmethod
    def _got_no_result(deferred):
        return Mismatch(
            _u('Failure result expected on %r, found no result instead'
               % (deferred,)))

    def match(self, deferred):
        return _on_deferred_result(
            deferred,
            on_success=partial(self._got_success, deferred),
            on_failure=partial(self._got_failure, deferred),
            on_no_result=partial(self._got_no_result, deferred),
        )


# XXX: The Twisted name is failureResultOf. Do we want to use that name?
#
# XXX: failureResultOf also takes an *args of expected exception types. Do we
# want to provide that?
def failed(matcher):
    # XXX: Docstring, with examples.
    return _Failed(matcher)

# TODO: helpers for adding matcher-based assertions in callbacks.
