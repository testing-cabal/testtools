# Copyright (c) 2010 Jonathan M. Lange. See LICENSE for details.

"""Tests for the DeferredRunTest single test execution logic."""

from testtools import (
    TestCase,
    )
from testtools.deferredruntest import (
    AsynchronousDeferredRunTest,
    DeferredNotFired,
    extract_result,
    not_reentrant,
    ReentryError,
    _Spinner,
    SynchronousDeferredRunTest,
    TimeoutError,
    trap_unhandled_errors,
    )
from testtools.tests.helpers import ExtendedTestResult
from testtools.matchers import (
    Equals,
    Is,
    )

from twisted.internet import defer
from twisted.python.failure import Failure


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


class TestSynchronousDeferredRunTest(TestCase):

    def make_result(self):
        return ExtendedTestResult()

    def make_runner(self, test):
        return SynchronousDeferredRunTest(test, test.exception_handlers)

    def test_success(self):
        class SomeCase(TestCase):
            def test_success(self):
                return defer.succeed(None)
        test = SomeCase('test_success')
        runner = self.make_runner(test)
        result = self.make_result()
        runner.run(result)
        self.assertThat(
            result._events, Equals([
                ('startTest', test),
                ('addSuccess', test),
                ('stopTest', test)]))

    def test_failure(self):
        class SomeCase(TestCase):
            def test_failure(self):
                return defer.maybeDeferred(self.fail, "Egads!")
        test = SomeCase('test_failure')
        runner = self.make_runner(test)
        result = self.make_result()
        runner.run(result)
        self.assertThat(
            [event[:2] for event in result._events], Equals([
                ('startTest', test),
                ('addFailure', test),
                ('stopTest', test)]))

    def test_setUp_followed_by_test(self):
        class SomeCase(TestCase):
            def setUp(self):
                super(SomeCase, self).setUp()
                return defer.succeed(None)
            def test_failure(self):
                return defer.maybeDeferred(self.fail, "Egads!")
        test = SomeCase('test_failure')
        runner = self.make_runner(test)
        result = self.make_result()
        runner.run(result)
        self.assertThat(
            [event[:2] for event in result._events], Equals([
                ('startTest', test),
                ('addFailure', test),
                ('stopTest', test)]))


class TestAsynchronousDeferredRunTest(TestCase):

    def make_reactor(self):
        from twisted.internet import reactor
        return reactor

    def make_result(self):
        return ExtendedTestResult()

    def make_runner(self, test, timeout=None):
        if timeout is None:
            timeout = self.make_timeout()
        return AsynchronousDeferredRunTest(
            test, test.exception_handlers, timeout=timeout)

    def make_timeout(self):
        return 0.005

    def test_setUp_returns_deferred_that_fires_later(self):
        # XXX: Explain how this test works.
        call_log = []
        marker = object()
        d = defer.Deferred().addCallback(call_log.append)
        class SomeCase(TestCase):
            def setUp(self):
                super(SomeCase, self).setUp()
                call_log.append('setUp')
                return d
            def test_something(self):
                call_log.append('test')
        def fire_deferred():
            self.assertThat(call_log, Equals(['setUp']))
            d.callback(marker)
        test = SomeCase('test_something')
        timeout = self.make_timeout()
        runner = self.make_runner(test, timeout=timeout)
        result = self.make_result()
        reactor = self.make_reactor()
        reactor.callLater(timeout, fire_deferred)
        runner.run(result)
        self.assertThat(call_log, Equals(['setUp', marker, 'test']))

    def test_calls_setUp_test_tearDown_in_sequence(self):
        # XXX: Explain how this test works.
        call_log = []
        a = defer.Deferred()
        b = defer.Deferred()
        c = defer.Deferred()
        class SomeCase(TestCase):
            def setUp(self):
                super(SomeCase, self).setUp()
                call_log.append('setUp')
                return a
            def test_success(self):
                call_log.append('test')
                return b
            def tearDown(self):
                super(SomeCase, self).tearDown()
                call_log.append('tearDown')
                return c
        a.addCallback(lambda x: call_log.append('a'))
        b.addCallback(lambda x: call_log.append('b'))
        c.addCallback(lambda x: call_log.append('c'))
        test = SomeCase('test_success')
        timeout = self.make_timeout()
        runner = self.make_runner(test, timeout)
        result = self.make_result()
        reactor = self.make_reactor()
        def fire_a():
            self.assertThat(call_log, Equals(['setUp']))
            a.callback(None)
        def fire_b():
            self.assertThat(call_log, Equals(['setUp', 'a', 'test']))
            b.callback(None)
        def fire_c():
            self.assertThat(
                call_log, Equals(['setUp', 'a', 'test', 'b', 'tearDown']))
            c.callback(None)
        reactor.callLater(timeout * 0.25, fire_a)
        reactor.callLater(timeout * 0.5, fire_b)
        reactor.callLater(timeout * 0.75, fire_c)
        runner.run(result)
        self.assertThat(
            call_log, Equals(['setUp', 'a', 'test', 'b', 'tearDown', 'c']))

    def test_clean_reactor(self):
        # If there's cruft left over in the reactor, the test fails.
        reactor = self.make_reactor()
        timeout = self.make_timeout()
        class SomeCase(TestCase):
            def test_cruft(self):
                reactor.callLater(timeout * 2.0, lambda: None)
        test = SomeCase('test_cruft')
        runner = self.make_runner(test, timeout)
        result = self.make_result()
        runner.run(result)
        error = result._events[1][2]
        result._events[1] = ('addError', test, None)
        self.assertThat(result._events, Equals(
            [('startTest', test),
             ('addError', test, None),
             ('stopTest', test)]))
        self.assertThat(list(error.keys()), Equals(['traceback']))

    def test_unhandled_error_from_deferred(self):
        # If there's a Deferred with an unhandled error, the test fails.
        class SomeCase(TestCase):
            def test_cruft(self):
                # Note we aren't returning the Deferred so that the error will
                # be unhandled.
                defer.maybeDeferred(lambda: 1/0)
        test = SomeCase('test_cruft')
        runner = self.make_runner(test)
        result = self.make_result()
        runner.run(result)
        error = result._events[1][2]
        result._events[1] = ('addError', test, None)
        self.assertThat(result._events, Equals(
            [('startTest', test),
             ('addError', test, None),
             ('stopTest', test)]))
        self.assertThat(list(error.keys()), Equals(['traceback']))

    def test_convenient_construction(self):
        # As a convenience method, AsynchronousDeferredRunTest has a
        # classmethod that returns an AsynchronousDeferredRunTest
        # factory. This factory has the same API as the RunTest constructor.
        reactor = object()
        timeout = object()
        handler = object()
        factory = AsynchronousDeferredRunTest.make_factory(reactor, timeout)
        runner = factory(self, [handler])
        self.assertIs(reactor, runner._reactor)
        self.assertIs(timeout, runner._timeout)
        self.assertIs(self, runner.case)
        self.assertEqual([handler], runner.handlers)


class TestRunInReactor(TestCase):

    def make_reactor(self):
        from twisted.internet import reactor
        return reactor

    def make_spinner(self, reactor=None):
        if reactor is None:
            reactor = self.make_reactor()
        return _Spinner(reactor)

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

    def test_timeout(self):
        # If the function takes too long to run, we raise a TimeoutError.
        timeout = self.make_timeout()
        self.assertRaises(
            TimeoutError,
            self.make_spinner().run, timeout, lambda: defer.Deferred())

    def test_clean_do_nothing(self):
        # If there's nothing going on in the reactor, then clean does nothing
        # and returns an empty list.
        spinner = self.make_spinner()
        result = spinner.clean()
        self.assertThat(result, Equals([]))

    def test_clean_delayed_call(self):
        # If there's a delayed call in the reactor, then clean cancels it and
        # returns an empty list.
        reactor = self.make_reactor()
        spinner = self.make_spinner(reactor)
        call = reactor.callLater(10, lambda: None)
        results = spinner.clean()
        self.assertThat(results, Equals([call]))
        self.assertThat(call.active(), Equals(False))

    def test_clean_delayed_call_cancelled(self):
        # If there's a delayed call that's just been cancelled, then it's no
        # longer there.
        reactor = self.make_reactor()
        spinner = self.make_spinner(reactor)
        call = reactor.callLater(10, lambda: None)
        call.cancel()
        results = spinner.clean()
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
        results = spinner.clean()
        self.assertThat(results, Equals([port]))


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
