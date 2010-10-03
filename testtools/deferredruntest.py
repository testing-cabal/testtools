# Copyright (c) 2010 Jonathan M. Lange. See LICENSE for details.

"""Individual test case execution for tests that return Deferreds."""

__all__ = [
    'AsynchronousDeferredRunTest',
    'SynchronousDeferredRunTest',
    ]

from testtools.runtest import RunTest

from twisted.internet import defer
from twisted.python.failure import Failure
from twisted.trial.unittest import TestCase


# XXX: Copied & pasted from somewhere else.  No tests in testtools.
def extract_result(deferred):
    """Extract the result from a fired deferred.

    It can happen that you have an API that returns Deferreds for
    compatibility with Twisted code, but is in fact synchronous, i.e. the
    Deferreds it returns have always fired by the time it returns.  In this
    case, you can use this function to convert the result back into the usual
    form for a synchronous API, i.e. the result itself or a raised exception.

    It would be very bad form to use this as some way of checking if a
    Deferred has fired.
    """
    failures = []
    successes = []
    deferred.addCallbacks(successes.append, failures.append)
    if len(failures) == 1:
        failures[0].raiseException()
    elif len(successes) == 1:
        return successes[0]
    else:
        # XXX: AssertionError might be inappropriate.  Perhaps we should have
        # a custom error message.
        raise AssertionError("%r has not fired yet." % (deferred,))


class SynchronousDeferredRunTest(RunTest):

    def _run_user(self, function, *args):
        d = defer.maybeDeferred(function, *args)
        def got_exception(failure):
            e = failure.value
            for exc_class, handler in self.handlers:
                if isinstance(e, exc_class):
                    self._exceptions.append(e)
                    return self.exception_caught
            return failure
        d.addErrback(got_exception)
        # XXX: Cheat!
        result = extract_result(d)
        return result


class AsynchronousDeferredRunTest(RunTest):

    def _run_user(self, function, *args):
        trial = TestCase()
        d = defer.maybeDeferred(function, *args)
        trial._wait(d)


class ReentryError(Exception):
    """Raised when we try to re-enter a function that forbids it."""


class TimeoutError(Exception):
    """Raised when run_in_reactor takes too long to run a function."""

_running = []

def run_in_reactor(reactor, timeout, function, *args, **kwargs):
    """Run 'function' in a reactor.

    If 'function' returns a Deferred, the reactor will keep spinning until the
    Deferred fires and its chain completes or until the timeout is reached --
    whichever comes first.
    """
    # XXX: The re-entrancy guard could probably be extracted into a helper.
    if _running:
        raise ReentryError()
    _running.append(None)
    results = []
    timeout_delayed_call = None
    def got_result(result):
        if timeout_delayed_call:
            timeout_delayed_call.cancel()
        results.append(result)
    def crash_reactor(ignored=None):
        reactor.crash()
    def timeout_error():
        e = TimeoutError(
            "%r took longer than %s seconds" % (function, timeout))
        results.append(Failure(e))
        crash_reactor()
    try:
        d = defer.maybeDeferred(function, *args, **kwargs)
        d.addBoth(got_result)
        d.addBoth(crash_reactor)
        timeout_delayed_call = reactor.callLater(timeout, timeout_error)
        reactor.run()
    finally:
        _running.pop()
    result = results[0]
    if isinstance(result, Failure):
        result.raiseException()
    return result
