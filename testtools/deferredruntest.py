# Copyright (c) 2010 Jonathan M. Lange. See LICENSE for details.

"""Individual test case execution for tests that return Deferreds.

This module is highly experimental and is liable to change in ways that cause
subtle failures in tests.  Use at your own peril.
"""

__all__ = [
    'assert_fails_with',
    'AsynchronousDeferredRunTest',
    'SynchronousDeferredRunTest',
    ]

import sys

from testtools.runtest import RunTest
from testtools._spinner import (
    extract_result,
    NoResultError,
    Spinner,
    TimeoutError,
    trap_unhandled_errors,
    )

from twisted.internet import defer


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

    def _log_user_exception(self, e):
        """Raise 'e' and report it as a user exception."""
        try:
            raise e
        except e.__class__:
            self._got_user_exception(sys.exc_info())

    def _run_core(self):
        spinner = Spinner(self._reactor)
        try:
            successful, unhandled = trap_unhandled_errors(
                spinner.run, self._timeout, self._run_deferred)
        except NoResultError:
            # We didn't get a result at all!  This could be for any number of
            # reasons, but most likely someone hit Ctrl-C during the test.
            raise KeyboardInterrupt
        except TimeoutError:
            # The function took too long to run.  No point reporting about
            # junk and we don't have any information about unhandled errors in
            # deferreds.  Report the timeout and skip to the end.
            self._log_user_exception(TimeoutError(self.case, self._timeout))
            return

        if unhandled:
            successful = False
            # XXX: Maybe we could log creator & invoker here as well if
            # present.
            for debug_info in unhandled:
                f = debug_info.failResult
                self._got_user_exception(
                    (f.type, f.value, f.tb), 'unhandled-error-in-deferred')
        junk = spinner.clear_junk()
        if junk:
            successful = False
            self._log_user_exception(UncleanReactorError(junk))
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


def assert_fails_with(d, *exc_types, **kwargs):
    """Assert that 'd' will fail with one of 'exc_types'.

    The normal way to use this is to return the result of 'assert_fails_with'
    from your unit test.

    Note that this function is experimental and unstable.  Use at your own
    peril; expect the API to change.

    :param d: A Deferred that is expected to fail.
    :param *exc_types: The exception types that the Deferred is expected to
        fail with.
    :param failureException: An optional keyword argument.  If provided, will
        raise that exception instead of `testtools.TestCase.failureException`.
    :return: A Deferred that will fail with an `AssertionError` if 'd' does
        not fail with one of the exception types.
    """
    failureException = kwargs.pop('failureException', None)
    if failureException is None:
        # Avoid circular imports.
        from testtools import TestCase
        failureException = TestCase.failureException
    expected_names = ", ".join(exc_type.__name__ for exc_type in exc_types)
    def got_success(result):
        raise failureException(
            "%s not raised (%r returned)" % (expected_names, result))
    def got_failure(failure):
        if failure.check(*exc_types):
            return failure.value
        raise failureException("%s raised instead of %s:\n %s" % (
            failure.type.__name__, expected_names, failure.getTraceback()))
    return d.addCallbacks(got_success, got_failure)


class UncleanReactorError(Exception):
    """Raised when the reactor has junk in it."""

    def __init__(self, junk):
        super(UncleanReactorError, self).__init__(
            "The reactor still thinks it needs to do things. Close all "
            "connections, kill all processes and make sure all delayed "
            "calls have either fired or been cancelled.  The management "
            "thanks you: %s"
            % map(repr, junk))
