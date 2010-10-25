# Copyright (c) 2010 Jonathan M. Lange. See LICENSE for details.

"""Tests for the evil Twisted reactor-spinning we do."""

import os
import signal

from testtools import (
    skipIf,
    TestCase,
    )
from testtools.matchers import (
    Equals,
    Is,
    )
from testtools._spinner import (
    DeferredNotFired,
    extract_result,
    NoResultError,
    not_reentrant,
    ReentryError,
    Spinner,
    StaleJunkError,
    TimeoutError,
    trap_unhandled_errors,
    )

from twisted.internet import defer
from twisted.python.failure import Failure


class TestNotReentrant(TestCase):

    def test_not_reentrant(self):
        # A function decorated as not being re-entrant will raise a
        # ReentryError if it is called while it is running.
        calls = []
        @not_reentrant
        def log_something():
            calls.append(None)
            if len(calls) < 5:
                log_something()
        self.assertRaises(ReentryError, log_something)
        self.assertEqual(1, len(calls))

    def test_deeper_stack(self):
        calls = []
        @not_reentrant
        def g():
            calls.append(None)
            if len(calls) < 5:
                f()
        @not_reentrant
        def f():
            calls.append(None)
            if len(calls) < 5:
                g()
        self.assertRaises(ReentryError, f)
        self.assertEqual(2, len(calls))


class TestExtractResult(TestCase):

    def test_not_fired(self):
        # extract_result raises DeferredNotFired if it's given a Deferred that
        # has not fired.
        self.assertRaises(DeferredNotFired, extract_result, defer.Deferred())

    def test_success(self):
        # extract_result returns the value of the Deferred if it has fired
        # successfully.
        marker = object()
        d = defer.succeed(marker)
        self.assertThat(extract_result(d), Equals(marker))

    def test_failure(self):
        # extract_result raises the failure's exception if it's given a
        # Deferred that is failing.
        try:
            1/0
        except ZeroDivisionError:
            f = Failure()
        d = defer.fail(f)
        self.assertRaises(ZeroDivisionError, extract_result, d)


class TestTrapUnhandledErrors(TestCase):

    def test_no_deferreds(self):
        marker = object()
        result, errors = trap_unhandled_errors(lambda: marker)
        self.assertEqual([], errors)
        self.assertIs(marker, result)

    def test_unhandled_error(self):
        failures = []
        def make_deferred_but_dont_handle():
            try:
                1/0
            except ZeroDivisionError:
                f = Failure()
                failures.append(f)
                defer.fail(f)
        result, errors = trap_unhandled_errors(make_deferred_but_dont_handle)
        self.assertIs(None, result)
        self.assertEqual(failures, [error.failResult for error in errors])


class TestRunInReactor(TestCase):

    def make_reactor(self):
        from twisted.internet import reactor
        return reactor

    def make_spinner(self, reactor=None):
        if reactor is None:
            reactor = self.make_reactor()
        return Spinner(reactor)

    def make_timeout(self):
        return 0.01

    def test_function_called(self):
        # run_in_reactor actually calls the function given to it.
        calls = []
        marker = object()
        self.make_spinner().run(self.make_timeout(), calls.append, marker)
        self.assertThat(calls, Equals([marker]))

    def test_return_value_returned(self):
        # run_in_reactor returns the value returned by the function given to
        # it.
        marker = object()
        result = self.make_spinner().run(self.make_timeout(), lambda: marker)
        self.assertThat(result, Is(marker))

    def test_exception_reraised(self):
        # If the given function raises an error, run_in_reactor re-raises that
        # error.
        self.assertRaises(
            ZeroDivisionError,
            self.make_spinner().run, self.make_timeout(), lambda: 1 / 0)

    def test_keyword_arguments(self):
        # run_in_reactor passes keyword arguments on.
        calls = []
        function = lambda *a, **kw: calls.extend([a, kw])
        self.make_spinner().run(self.make_timeout(), function, foo=42)
        self.assertThat(calls, Equals([(), {'foo': 42}]))

    def test_not_reentrant(self):
        # run_in_reactor raises an error if it is called inside another call
        # to run_in_reactor.
        spinner = self.make_spinner()
        self.assertRaises(
            ReentryError,
            spinner.run, self.make_timeout(),
            spinner.run, self.make_timeout(), lambda: None)

    def test_deferred_value_returned(self):
        # If the given function returns a Deferred, run_in_reactor returns the
        # value in the Deferred at the end of the callback chain.
        marker = object()
        result = self.make_spinner().run(
            self.make_timeout(), lambda: defer.succeed(marker))
        self.assertThat(result, Is(marker))

    def test_preserve_signal_handler(self):
        signals = ['SIGINT', 'SIGTERM', 'SIGCHLD']
        signals = filter(
            None, (getattr(signal, name, None) for name in signals))
        for sig in signals:
            self.addCleanup(signal.signal, sig, signal.getsignal(sig))
        new_hdlrs = [lambda *a: None, lambda *a: None, lambda *a: None]
        for sig, hdlr in zip(signals, new_hdlrs):
            signal.signal(sig, hdlr)
        spinner = self.make_spinner()
        spinner.run(self.make_timeout(), lambda: None)
        self.assertEqual(new_hdlrs, map(signal.getsignal, signals))

    def test_timeout(self):
        # If the function takes too long to run, we raise a TimeoutError.
        timeout = self.make_timeout()
        self.assertRaises(
            TimeoutError,
            self.make_spinner().run, timeout, lambda: defer.Deferred())

    def test_no_junk_by_default(self):
        # If the reactor hasn't spun yet, then there cannot be any junk.
        spinner = self.make_spinner()
        self.assertThat(spinner.get_junk(), Equals([]))

    def test_clean_do_nothing(self):
        # If there's nothing going on in the reactor, then clean does nothing
        # and returns an empty list.
        spinner = self.make_spinner()
        result = spinner._clean()
        self.assertThat(result, Equals([]))

    def test_clean_delayed_call(self):
        # If there's a delayed call in the reactor, then clean cancels it and
        # returns an empty list.
        reactor = self.make_reactor()
        spinner = self.make_spinner(reactor)
        call = reactor.callLater(10, lambda: None)
        results = spinner._clean()
        self.assertThat(results, Equals([call]))
        self.assertThat(call.active(), Equals(False))

    def test_clean_delayed_call_cancelled(self):
        # If there's a delayed call that's just been cancelled, then it's no
        # longer there.
        reactor = self.make_reactor()
        spinner = self.make_spinner(reactor)
        call = reactor.callLater(10, lambda: None)
        call.cancel()
        results = spinner._clean()
        self.assertThat(results, Equals([]))

    def test_clean_selectables(self):
        # If there's still a selectable (e.g. a listening socket), then
        # clean() removes it from the reactor's registry.
        #
        # Note that the socket is left open. This emulates a bug in trial.
        from twisted.internet.protocol import ServerFactory
        reactor = self.make_reactor()
        spinner = self.make_spinner(reactor)
        port = reactor.listenTCP(0, ServerFactory())
        spinner.run(self.make_timeout(), lambda: None)
        results = spinner.get_junk()
        self.assertThat(results, Equals([port]))

    def test_clean_running_threads(self):
        import threading
        import time
        current_threads = list(threading.enumerate())
        reactor = self.make_reactor()
        timeout = self.make_timeout()
        spinner = self.make_spinner(reactor)
        spinner.run(timeout, reactor.callInThread, time.sleep, timeout / 2.0)
        self.assertThat(list(threading.enumerate()), Equals(current_threads))

    def test_leftover_junk_available(self):
        # If 'run' is given a function that leaves the reactor dirty in some
        # way, 'run' will clean up the reactor and then store information
        # about the junk. This information can be got using get_junk.
        from twisted.internet.protocol import ServerFactory
        reactor = self.make_reactor()
        spinner = self.make_spinner(reactor)
        port = spinner.run(
            self.make_timeout(), reactor.listenTCP, 0, ServerFactory())
        self.assertThat(spinner.get_junk(), Equals([port]))

    def test_will_not_run_with_previous_junk(self):
        # If 'run' is called and there's still junk in the spinner's junk
        # list, then the spinner will refuse to run.
        from twisted.internet.protocol import ServerFactory
        reactor = self.make_reactor()
        spinner = self.make_spinner(reactor)
        timeout = self.make_timeout()
        spinner.run(timeout, reactor.listenTCP, 0, ServerFactory())
        self.assertRaises(
            StaleJunkError, spinner.run, timeout, lambda: None)

    def test_clear_junk_clears_previous_junk(self):
        # If 'run' is called and there's still junk in the spinner's junk
        # list, then the spinner will refuse to run.
        from twisted.internet.protocol import ServerFactory
        reactor = self.make_reactor()
        spinner = self.make_spinner(reactor)
        timeout = self.make_timeout()
        port = spinner.run(timeout, reactor.listenTCP, 0, ServerFactory())
        junk = spinner.clear_junk()
        self.assertThat(junk, Equals([port]))
        self.assertThat(spinner.get_junk(), Equals([]))

    @skipIf(os.name != "posix", "Sending SIGINT with os.kill is posix only")
    def test_sigint_raises_no_result_error(self):
        # If we get a SIGINT during a run, we raise NoResultError.
        SIGINT = getattr(signal, 'SIGINT', None)
        if not SIGINT:
            self.skipTest("SIGINT not available")
        reactor = self.make_reactor()
        spinner = self.make_spinner(reactor)
        timeout = self.make_timeout()
        reactor.callLater(timeout, os.kill, os.getpid(), SIGINT)
        self.assertRaises(
            NoResultError, spinner.run, timeout * 5, defer.Deferred)
        self.assertEqual([], spinner._clean())

    @skipIf(os.name != "posix", "Sending SIGINT with os.kill is posix only")
    def test_sigint_raises_no_result_error_second_time(self):
        # If we get a SIGINT during a run, we raise NoResultError.  This test
        # is exactly the same as test_sigint_raises_no_result_error, and
        # exists to make sure we haven't futzed with state.
        self.test_sigint_raises_no_result_error()

    @skipIf(os.name != "posix", "Sending SIGINT with os.kill is posix only")
    def test_fast_sigint_raises_no_result_error(self):
        # If we get a SIGINT during a run, we raise NoResultError.
        SIGINT = getattr(signal, 'SIGINT', None)
        if not SIGINT:
            self.skipTest("SIGINT not available")
        reactor = self.make_reactor()
        spinner = self.make_spinner(reactor)
        timeout = self.make_timeout()
        reactor.callWhenRunning(os.kill, os.getpid(), SIGINT)
        self.assertRaises(
            NoResultError, spinner.run, timeout * 5, defer.Deferred)
        self.assertEqual([], spinner._clean())

    @skipIf(os.name != "posix", "Sending SIGINT with os.kill is posix only")
    def test_fast_sigint_raises_no_result_error_second_time(self):
        self.test_fast_sigint_raises_no_result_error()


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
