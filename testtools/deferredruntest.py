# Copyright (c) 2010-2015 testtools developers. See LICENSE for details.

"""Individual test case execution for tests that return Deferreds.

This module is highly experimental and is liable to change in ways that cause
subtle failures in tests.  Use at your own peril.
"""

__all__ = [
    'assert_fails_with',
    'AsynchronousDeferredRunTest',
    'AsynchronousDeferredRunTestForBrokenTwisted',
    'SynchronousDeferredRunTest',
    ]

import sys

from fixtures import Fixture

from testtools.compat import StringIO
from testtools.content import Content, text_content
from testtools.content_type import UTF8_TEXT
from testtools.runtest import RunTest
from testtools._spinner import (
    extract_result,
    NoResultError,
    Spinner,
    TimeoutError,
    trap_unhandled_errors,
    )

from twisted.internet import defer
try:
    from twisted.logger import globalLogPublisher
except ImportError:
    globalLogPublisher = None
from twisted.python import log
try:
    from twisted.trial.unittest import _LogObserver
except ImportError:
    from twisted.trial._synctest import _LogObserver


class _DeferredRunTest(RunTest):
    """Base for tests that return Deferreds."""

    def _got_user_failure(self, failure, tb_label='traceback'):
        """We got a failure from user code."""
        return self._got_user_exception(
            (failure.type, failure.value, failure.getTracebackObject()),
            tb_label=tb_label)


class SynchronousDeferredRunTest(_DeferredRunTest):
    """Runner for tests that return synchronous Deferreds."""

    def _run_user(self, function, *args):
        d = defer.maybeDeferred(function, *args)
        d.addErrback(self._got_user_failure)
        result = extract_result(d)
        return result


def _get_global_publisher_and_observers():
    """Return ``(log_publisher, observers)``.

    Twisted 15.2.0 changed the logging framework. This method will always
    return a tuple of the global log publisher and all observers associated
    with that publisher.
    """
    if globalLogPublisher is not None:
        # Twisted >= 15.2.0, with the new twisted.logger framework.
        # log.theLogPublisher.observers will only contain legacy observers;
        # we need to look at globalLogPublisher._observers, which contains
        # both legacy and modern observers, and add and remove them via
        # globalLogPublisher.  However, we must still add and remove the
        # observers we want to run with via log.theLogPublisher, because
        # _LogObserver may consider old keys and require them to be mapped.
        publisher = globalLogPublisher
        return (publisher, list(publisher._observers))
    else:
        publisher = log.theLogPublisher
        return (publisher, list(publisher.observers))


def _add_observers(publisher, observers):
    for observer in observers:
        publisher.addObserver(observer)


def _remove_observers(publisher, observers):
    for observer in observers:
        publisher.removeObserver(observer)


class NoTwistedLogObservers(Fixture):
    """Completely but temporarily remove all Twisted log observers."""

    # XXX: Direct tests. Currently tested indirectly via
    # run_with_log_observers.

    def _setUp(self):
        publisher, real_observers = _get_global_publisher_and_observers()
        _remove_observers(publisher, real_observers)
        self.addCleanup(_add_observers, publisher, real_observers)


class TwistedLogObservers(Fixture):
    """Temporarily add Twisted log observers."""

    # XXX: Direct tests. Currently tested indirectly via
    # run_with_log_observers.

    def __init__(self, observers):
        super(TwistedLogObservers, self).__init__()
        self._observers = observers
        self._log_publisher = log.theLogPublisher

    def _setUp(self):
        for observer in self._observers:
            self._log_publisher.addObserver(observer)
            self.addCleanup(self._log_publisher.removeObserver, observer)


class ErrorObserver(Fixture):
    """Capture logged errors.

    :ivar logged_errors: list of errors caught while fixture active.
    """

    def __init__(self, error_observer):
        super(ErrorObserver, self).__init__()
        self._error_observer = error_observer
        self.logged_errors = []

    def _setUp(self):
        self.logged_errors = []
        self.useFixture(TwistedLogObservers([self._error_observer.gotEvent]))
        self.addCleanup(self._store_logged_errors)

    def _store_logged_errors(self):
        self.logged_errors = self.flush_logged_errors()

    def flush_logged_errors(self, *error_types):
        """Clear errors of the given types from the logs.

        If no errors provided, clear all errors.

        :return: An iterable of errors removed from the logs.
        """
        return self._error_observer.flushErrors(*error_types)


class CaptureTwistedLogs(Fixture):
    """Capture all the Twisted logs and add them as a detail."""

    def __init__(self):
        super(CaptureTwistedLogs, self).__init__()
        self._twisted_log = StringIO()

    def _setUp(self):
        full_observer = log.FileLogObserver(self._twisted_log)
        self.useFixture(TwistedLogObservers([full_observer.emit]))
        # XXX: This isn't actually *useful* yet because Fixture clears details
        # when it exits a context manager (which is the only way we currently
        # use it).
        self.addCleanup(self.addDetail, 'twisted-log', self.get_twisted_log())

    def get_twisted_log(self):
        """Return the contents of the Twisted log."""
        return Content(UTF8_TEXT, self._twisted_log.getvalue)


def run_with_log_observers(observers, function, *args, **kwargs):
    """Run 'function' with the given Twisted log observers."""
    # XXX: DEPRECATE THIS
    with NoTwistedLogObservers():
        with TwistedLogObservers(observers):
            return function(*args, **kwargs)


# Observer of the Twisted log that we install during tests.
#
# This is a global so that users can call flush_logged_errors errors in their
# test cases.
_log_observer = _LogObserver()


def flush_logged_errors(*error_types):
    # XXX: I would like to deprecate this in favour of
    # ErrorObserver.flush_logged_errors so that I can avoid mutable global
    # state. However, I don't know how to make the correct instance of
    # ErrorObserver.flush_logged_errors available to the end user. I also
    # don't yet have a clear deprecation/migration path.
    return _log_observer.flushErrors(*error_types)


class AsynchronousDeferredRunTest(_DeferredRunTest):
    """Runner for tests that return Deferreds that fire asynchronously.

    That is, this test runner assumes that the Deferreds will only fire if the
    reactor is left to spin for a while.

    Do not rely too heavily on the nuances of the behaviour of this class.
    What it does to the reactor is black magic, and if we can find nicer ways
    of doing it we will gladly break backwards compatibility.

    This is highly experimental code.  Use at your own risk.
    """

    def __init__(self, case, handlers=None, last_resort=None, reactor=None,
                 timeout=0.005, debug=False):
        """Construct an `AsynchronousDeferredRunTest`.

        Please be sure to always use keyword syntax, not positional, as the
        base class may add arguments in future - and for core code
        compatibility with that we have to insert them before the local
        parameters.

        :param case: The `TestCase` to run.
        :param handlers: A list of exception handlers (ExceptionType, handler)
            where 'handler' is a callable that takes a `TestCase`, a
            ``testtools.TestResult`` and the exception raised.
        :param last_resort: Handler to call before re-raising uncatchable
            exceptions (those for which there is no handler).
        :param reactor: The Twisted reactor to use.  If not given, we use the
            default reactor.
        :param timeout: The maximum time allowed for running a test.  The
            default is 0.005s.
        :param debug: Whether or not to enable Twisted's debugging.  Use this
            to get information about unhandled Deferreds and left-over
            DelayedCalls.  Defaults to False.
        """
        super(AsynchronousDeferredRunTest, self).__init__(
            case, handlers, last_resort)
        if reactor is None:
            from twisted.internet import reactor
        self._reactor = reactor
        self._timeout = timeout
        self._debug = debug

    @classmethod
    def make_factory(cls, reactor=None, timeout=0.005, debug=False):
        """Make a factory that conforms to the RunTest factory interface."""
        # This is horrible, but it means that the return value of the method
        # will be able to be assigned to a class variable *and* also be
        # invoked directly.
        class AsynchronousDeferredRunTestFactory:
            def __call__(self, case, handlers=None, last_resort=None):
                return cls(case, handlers, last_resort, reactor, timeout, debug)
        return AsynchronousDeferredRunTestFactory()

    @defer.deferredGenerator
    def _run_cleanups(self):
        """Run the cleanups on the test case.

        We expect that the cleanups on the test case can also return
        asynchronous Deferreds.  As such, we take the responsibility for
        running the cleanups, rather than letting TestCase do it.
        """
        while self.case._cleanups:
            f, args, kwargs = self.case._cleanups.pop()
            d = defer.maybeDeferred(f, *args, **kwargs)
            thing = defer.waitForDeferred(d)
            yield thing
            try:
                thing.getResult()
            except Exception:
                exc_info = sys.exc_info()
                self.case._report_traceback(exc_info)
                last_exception = exc_info[1]
        yield last_exception

    def _make_spinner(self):
        """Make the `Spinner` to be used to run the tests."""
        return Spinner(self._reactor, debug=self._debug)

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

    def _blocking_run_deferred(self, spinner):
        try:
            return trap_unhandled_errors(
                spinner.run, self._timeout, self._run_deferred)
        except NoResultError:
            # We didn't get a result at all!  This could be for any number of
            # reasons, but most likely someone hit Ctrl-C during the test.
            raise KeyboardInterrupt
        except TimeoutError:
            # The function took too long to run.
            self._log_user_exception(TimeoutError(self.case, self._timeout))
            return False, []

    def _run_core(self):
        # XXX: Blatting over the namespace of the test case isn't a nice thing
        # to do. Find a better way of communicating between runtest and test
        # case.
        self.case.reactor = self._reactor
        spinner = self._make_spinner()

        # XXX: jml: Review test coverage to see if this is sane.
        with NoTwistedLogObservers():
            # XXX: jml: Maybe try self.case.useFixture(CaptureTwistedLogs())?
            with CaptureTwistedLogs() as capture_logs:
                with ErrorObserver(_log_observer) as error_fixture:
                    successful, unhandled = self._blocking_run_deferred(
                        spinner)

                for logged_error in error_fixture.logged_errors:
                    successful = False
                    self._got_user_failure(
                        logged_error, tb_label='logged-error')

            # XXX: Duplicates the 'twisted-log' name from the fixture
            # because Fixture clears details after the 'with' block.
            self.case.addDetail(
                'twisted-log', capture_logs.get_twisted_log())

        if unhandled:
            successful = False
            for debug_info in unhandled:
                f = debug_info.failResult
                info = debug_info._getDebugTracebacks()
                if info:
                    self.case.addDetail(
                        'unhandled-error-in-deferred-debug',
                        text_content(info))
                self._got_user_failure(f, 'unhandled-error-in-deferred')

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
        d = defer.maybeDeferred(function, *args)
        return d.addErrback(self._got_user_failure)


class AsynchronousDeferredRunTestForBrokenTwisted(AsynchronousDeferredRunTest):
    """Test runner that works around Twisted brokenness re reactor junk.

    There are many APIs within Twisted itself where a Deferred fires but
    leaves cleanup work scheduled for the reactor to do.  Arguably, many of
    these are bugs.  This runner iterates the reactor event loop a number of
    times after every test, in order to shake out these buggy-but-commonplace
    events.
    """

    def _make_spinner(self):
        spinner = super(
            AsynchronousDeferredRunTestForBrokenTwisted, self)._make_spinner()
        spinner._OBLIGATORY_REACTOR_ITERATIONS = 2
        return spinner


def assert_fails_with(d, *exc_types, **kwargs):
    """Assert that 'd' will fail with one of 'exc_types'.

    The normal way to use this is to return the result of 'assert_fails_with'
    from your unit test.

    Note that this function is experimental and unstable.  Use at your own
    peril; expect the API to change.

    :param d: A Deferred that is expected to fail.
    :param exc_types: The exception types that the Deferred is expected to
        fail with.
    :param failureException: An optional keyword argument.  If provided, will
        raise that exception instead of
        ``testtools.TestCase.failureException``.
    :return: A Deferred that will fail with an ``AssertionError`` if 'd' does
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
        Exception.__init__(self,
            "The reactor still thinks it needs to do things. Close all "
            "connections, kill all processes and make sure all delayed "
            "calls have either fired or been cancelled:\n%s"
            % ''.join(map(self._get_junk_info, junk)))

    def _get_junk_info(self, junk):
        from twisted.internet.base import DelayedCall
        if isinstance(junk, DelayedCall):
            ret = str(junk)
        else:
            ret = repr(junk)
        return '  %s\n' % (ret,)
