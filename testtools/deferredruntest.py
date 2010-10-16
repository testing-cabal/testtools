# Copyright (c) 2010 Jonathan M. Lange. See LICENSE for details.

"""Individual test case execution for tests that return Deferreds.

This module is highly experimental and is liable to change in ways that cause
subtle failures in tests.  Use at your own peril.
"""

__all__ = [
    'AsynchronousDeferredRunTest',
    'SynchronousDeferredRunTest',
    ]

import sys

from testtools.runtest import RunTest
from testtools._spinner import (
    extract_result,
    NoResultError,
    Spinner,
    trap_unhandled_errors,
    UnhandledErrorInDeferred,
    )

from twisted.internet import defer


# TODO: Need a helper to replace Trial's assertFailure.

# TODO: Need a conversion guide for flushLoggedErrors

class SynchronousDeferredRunTest(RunTest):
    """Runner for tests that return synchronous Deferreds."""

    def _run_user(self, function, *args):
        d = defer.maybeDeferred(function, *args)
        def got_exception(failure):
            return self._got_user_exception(
                (failure.type, failure.value, failure.tb))
        d.addErrback(got_exception)
        result = extract_result(d)
        return result


class AsynchronousDeferredRunTest(RunTest):
    """Runner for tests that return Deferreds that fire asynchronously.

    That is, this test runner assumes that the Deferreds will only fire if the
    reactor is left to spin for a while.

    Do not rely too heavily on the nuances of the behaviour of this class.
    What it does to the reactor is black magic, and if we can find nicer ways
    of doing it we will gladly break backwards compatibility.

    This is highly experimental code.  Use at your own risk.
    """

    def __init__(self, case, handlers=None, reactor=None, timeout=0.005):
        """Construct an `AsynchronousDeferredRunTest`.

        :param case: The `testtools.TestCase` to run.
        :param handlers: A list of exception handlers (ExceptionType, handler)
            where 'handler' is a callable that takes a `TestCase`, a
            `TestResult` and the exception raised.
        :param reactor: The Twisted reactor to use.  If not given, we use the
            default reactor.
        :param timeout: The maximum time allowed for running a test.  The
            default is 0.005s.
        """
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
            except Exception:
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
        spinner = Spinner(self._reactor)
        try:
            # XXX: Right now, TimeoutErrors are re-raised, causing the test
            # runner to crash.  We probably just want to record them like test
            # errors.
            successful, unhandled = trap_unhandled_errors(
                spinner.run, self._timeout, self._run_deferred)
        except NoResultError:
            # We didn't get a result at all!  This could be for any number of
            # reasons, but most likely someone hit Ctrl-C during the test.
            raise KeyboardInterrupt
        if unhandled:
            successful = False
            # TODO: Actually, rather than raising this with a special error,
            # we could add a traceback for each unhandled Deferred, or
            # something like that.  Would be way more helpful than just a list
            # of the reprs of the failures.
            try:
                raise UnhandledErrorInDeferred(unhandled)
            except UnhandledErrorInDeferred:
                self._got_user_exception(sys.exc_info())
        junk = spinner.clear_junk()
        if junk:
            successful = False
            try:
                raise UncleanReactorError(junk)
            except UncleanReactorError:
                self._got_user_exception(sys.exc_info())
        if successful:
            self.result.addSuccess(self.case, details=self.case.getDetails())

    def _run_user(self, function, *args):
        """Run a user-supplied function.

        This just makes sure that it returns a Deferred, regardless of how the
        user wrote it.
        """
        return defer.maybeDeferred(
            super(AsynchronousDeferredRunTest, self)._run_user,
            function, *args)


class UncleanReactorError(Exception):
    """Raised when the reactor has junk in it."""

    def __init__(self, junk):
        super(UncleanReactorError, self).__init__(
            "The reactor still thinks it needs to do things. Close all "
            "connections, kill all processes and make sure all delayed "
            "calls have either fired or been cancelled.  The management "
            "thanks you: %s"
            % map(repr, junk))


