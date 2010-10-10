# Copyright (c) 2010 Jonathan M. Lange. See LICENSE for details.

"""Individual test case execution for tests that return Deferreds."""

__all__ = [
    'AsynchronousDeferredRunTest',
    'SynchronousDeferredRunTest',
    ]

import signal
import sys

from testtools.runtest import RunTest

from twisted.internet import defer
from twisted.internet.interfaces import IReactorThreads
from twisted.python.failure import Failure
from twisted.python.util import mergeFunctionMetadata


class DeferredNotFired(Exception):
    """Raised when we extract a result from a Deferred that's not fired yet."""


class UnhandledErrorInDeferred(Exception):
    """Raised when there are unhandlede errors in Deferreds.

    If you are getting this error then you are probably either not returning a
    Deferred from a function that makes one, or you are not adding an errback
    to a Deferred.  Or both.  Use `Deferred.DEBUG` to get more information.
    """

    def __init__(self, debug_infos):
        super(UnhandledErrorInDeferred, self).__init__(
            "Unhandled error in Deferreds: %r" % (
                [info.failResult for info in debug_infos]))


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
        raise DeferredNotFired("%r has not fired yet." % (deferred,))


def trap_unhandled_errors(function, *args, **kwargs):
    """Run a function, trapping any unhandled errors in Deferreds.

    Assumes that 'function' will have handled any errors in Deferreds by the
    time it is complete.  This is almost never true of any Twisted code, since
    you can never tell when someone has added an errback to a Deferred.

    If 'function' raises, then don't bother doing any unhandled error
    jiggery-pokery, since something horrible has probably happened anyway.

    :return: A tuple of '(result, error)', where 'result' is the value returned
        by 'function' and 'error' is a list of `defer.DebugInfo` objects that
        have unhandled errors in Deferreds.
    """
    real_DebugInfo = defer.DebugInfo
    debug_infos = []
    def DebugInfo():
        info = real_DebugInfo()
        debug_infos.append(info)
        return info
    defer.DebugInfo = DebugInfo
    try:
        result = function(*args, **kwargs)
    finally:
        defer.DebugInfo = real_DebugInfo
    errors = []
    for info in debug_infos:
        if info.failResult is not None:
            errors.append(info)
            # Disable the destructor that logs to error. We are already
            # catching the error here.
            info.__del__ = lambda: None
    return result, errors


class SynchronousDeferredRunTest(RunTest):
    """Runner for tests that return synchronous Deferreds."""

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
        result = extract_result(d)
        return result


# XXX: Still need to demonstrate how this can be hooked up to an actual test.

class AsynchronousDeferredRunTest(RunTest):
    """Runner for tests that return Deferreds that fire asynchronously.

    That is, this test runner assumes that the Deferreds will only fire if the
    reactor is left to spin for a while.

    Do not rely too heavily on the nuances of the behaviour of this class.
    What it does to the reactor is black magic, and if we can find nicer ways
    of doing it we will gladly break backwards compatibility.
    """

    def __init__(self, case, handlers=None, reactor=None, timeout=0.005):
        super(AsynchronousDeferredRunTest, self).__init__(case, handlers)
        if reactor is None:
            from twisted.internet import reactor
        self._reactor = reactor
        self._timeout = timeout

    @classmethod
    def make_factory(cls, reactor, timeout):
        return lambda case, handlers=None: AsynchronousDeferredRunTest(
            case, handlers, reactor, timeout)

    @defer.inlineCallbacks
    def _run_cleanups(self):
        """Run the cleanups on the test case.

        We expect that the cleanups on the test case can also return
        asynchronous Deferreds.  As such, we take the responsibility for
        running the cleanups, rather than letting TestCase do it.
        """
        while self.case._cleanups:
            f, args, kwargs = self.case._cleanups.pop()
            try:
                yield defer.maybeDeferred(f, *args, **kwargs)
            except:
                exc_info = sys.exc_info()
                self.case._report_traceback(exc_info)
                last_exception = exc_info[1]
        defer.returnValue(last_exception)

    def _run_deferred(self):
        """Run the test, assuming everything in it is Deferred-returning.

        This should return a Deferred that fires with True if the test was
        successful and False if the test was not successful.  It should *not*
        call addSuccess on the result, because there's reactor clean up that
        we needs to be done afterwards.
        """
        fails = []

        def fail_if_exception_caught(exception_caught):
            if self.exception_caught == exception_caught:
                fails.append(None)

        def clean_up(ignored=None):
            """Run the cleanups."""
            d = self._run_cleanups()
            def clean_up_done(result):
                if result is not None:
                    self._exceptions.append(result)
                    fails.append(None)
            return d.addCallback(clean_up_done)

        def set_up_done(exception_caught):
            """Set up is done, either clean up or run the test."""
            if self.exception_caught == exception_caught:
                fails.append(None)
                return clean_up()
            else:
                d = self._run_user(self.case._run_test_method, self.result)
                d.addCallback(fail_if_exception_caught)
                d.addBoth(tear_down)
                return d

        def tear_down(ignored):
            d = self._run_user(self.case._run_teardown, self.result)
            d.addCallback(fail_if_exception_caught)
            d.addBoth(clean_up)
            return d

        d = self._run_user(self.case._run_setup, self.result)
        d.addCallback(set_up_done)
        d.addBoth(lambda ignored: len(fails) == 0)
        return d

    def _run_core(self):
        spinner = _Spinner(self._reactor)
        # XXX: This can call addError on result multiple times. Not sure if
        # this is a good idea.
        successful, unhandled = trap_unhandled_errors(
            spinner.run, self._timeout, self._run_deferred)
        if unhandled:
            successful = False
            try:
                raise UnhandledErrorInDeferred(unhandled)
            except UnhandledErrorInDeferred:
                self._got_user_exception(sys.exc_info())
        junk = spinner.clean()
        if junk:
            successful = False
            try:
                raise UncleanReactorError(junk)
            except UncleanReactorError:
                self._got_user_exception(sys.exc_info())
        if successful:
            self.result.addSuccess(self.case, details=self.case.getDetails())

    def _run_user(self, function, *args):
        # XXX: I think this traps KeyboardInterrupt, and I think this is a bad
        # thing. Perhaps we should have a maybeDeferred-like thing that
        # re-raises KeyboardInterrupt. Or, we should have our own exception
        # handler that stops the test run in the case of KeyboardInterrupt. But
        # of course, the reactor installs a SIGINT handler anyway.
        return defer.maybeDeferred(
            super(AsynchronousDeferredRunTest, self)._run_user,
            function, *args)


class ReentryError(Exception):
    """Raised when we try to re-enter a function that forbids it."""

    def __init__(self, function):
        super(ReentryError, self).__init__(
            "%r in not re-entrant but was called within a call to itself."
            % (function,))


class UncleanReactorError(Exception):
    """Raised when the reactor has junk in it."""

    def __init__(self, junk):
        super(UncleanReactorError, self).__init__(
            "The reactor still thinks it needs to do things. Close all "
            "connections, kill all processes and make sure all delayed "
            "calls have either fired or been cancelled.  The management "
            "thanks you: %s"
            % map(repr, junk))


def not_reentrant(function, _calls={}):
    """Decorates a function as not being re-entrant.

    The decorated function will raise an error if called from within itself.
    """
    def decorated(*args, **kwargs):
        if _calls.get(function, False):
            raise ReentryError(function)
        _calls[function] = True
        try:
            return function(*args, **kwargs)
        finally:
            _calls[function] = False
    return mergeFunctionMetadata(function, decorated)


class TimeoutError(Exception):
    """Raised when run_in_reactor takes too long to run a function."""


class _Spinner(object):
    """Spin the reactor until a function is done.

    This class emulates the behaviour of twisted.trial in that it grotesquely
    and horribly spins the Twisted reactor while a function is running, and
    then kills the reactor when that function is complete and all the
    callbacks in its chains are done.
    """

    _UNSET = object()

    # Signals that we save and restore for each spin.
    _PRESERVED_SIGNALS = [
        signal.SIGINT,
        signal.SIGTERM,
        signal.SIGCHLD,
        ]

    def __init__(self, reactor):
        self._reactor = reactor
        self._timeout_call = None
        self._success = self._UNSET
        self._failure = self._UNSET
        self._saved_signals = []

    def _cancel_timeout(self):
        if self._timeout_call:
            self._timeout_call.cancel()

    def _get_result(self):
        if self._failure is not self._UNSET:
            self._failure.raiseException()
        if self._success is not self._UNSET:
            return self._success
        raise AssertionError("Tried to get result when no result is available.")

    def _got_failure(self, result):
        self._cancel_timeout()
        self._failure = result

    def _got_success(self, result):
        self._cancel_timeout()
        self._success = result

    def _stop_reactor(self, ignored=None):
        """Stop the reactor!"""
        self._reactor.crash()

    def _timed_out(self, function, timeout):
        e = TimeoutError(
            "%r took longer than %s seconds" % (function, timeout))
        self._failure = Failure(e)
        self._stop_reactor()

    def clean(self):
        """Clean up any junk in the reactor."""
        junk = []
        for delayed_call in self._reactor.getDelayedCalls():
            delayed_call.cancel()
            junk.append(delayed_call)
        for selectable in self._reactor.removeAll():
            # Twisted sends a 'KILL' signal to selectables that provide
            # IProcessTransport.  Since only _dumbwin32proc processes do this,
            # we aren't going to bother.
            junk.append(selectable)
        # XXX: Not tested. Not sure that the cost of testing this reliably
        # outweighs the benefits.
        if IReactorThreads.providedBy(self._reactor):
            self._reactor.suggestThreadPoolSize(0)
            if self._reactor.threadpool is not None:
                self._reactor._stopThreadPool()
        return junk

    def _save_signals(self):
        self._saved_signals = [
            (sig, signal.getsignal(sig)) for sig in self._PRESERVED_SIGNALS]

    def _restore_signals(self):
        for sig, hdlr in self._saved_signals:
            signal.signal(sig, hdlr)
        self._saved_signals = []

    @not_reentrant
    def run(self, timeout, function, *args, **kwargs):
        """Run 'function' in a reactor.

        If 'function' returns a Deferred, the reactor will keep spinning until
        the Deferred fires and its chain completes or until the timeout is
        reached -- whichever comes first.
        """
        self._save_signals()
        self._timeout_call = self._reactor.callLater(
            timeout, self._timed_out, function, timeout)
        def run_function():
            d = defer.maybeDeferred(function, *args, **kwargs)
            d.addCallbacks(self._got_success, self._got_failure)
            d.addBoth(self._stop_reactor)
        self._reactor.callWhenRunning(run_function)
        self._reactor.run()
        self._restore_signals()
        return self._get_result()
