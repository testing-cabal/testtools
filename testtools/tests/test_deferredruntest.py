# Copyright (c) 2010 Jonathan M. Lange. See LICENSE for details.

"""Tests for the DeferredRunTest single test execution logic."""

from testtools import (
    TestCase,
    )
from testtools.deferredruntest import (
    AsynchronousDeferredRunTest,
    ReentryError,
    _Spinner,
    SynchronousDeferredRunTest,
    TimeoutError,
    )
from testtools.tests.helpers import ExtendedTestResult
from testtools.matchers import (
    Equals,
    Is,
    )

from twisted.internet import defer


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

    def make_runner(self, test):
        return AsynchronousDeferredRunTest(test, test.exception_handlers)

    def disabled_test_setUp_returns_deferred_that_fires_later(self):
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
        runner = self.make_runner(test)
        result = self.make_result()
        reactor = self.make_reactor()
        reactor.callLater(1, fire_deferred)
        runner.run(result)
        self.assertThat(call_log, Equals(['setUp', marker, 'test']))

    def disabled_test_calls_setUp_test_tearDown_in_sequence(self):
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
        runner = self.make_runner(test)
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
        reactor.callLater(1, fire_a)
        reactor.callLater(2, fire_b)
        reactor.callLater(3, fire_c)
        runner.run(result)
        # XXX: We ought to catch unhandled errors in Deferreds.  This means
        # hooking into Twisted's logging system.
        self.assertThat(
            call_log, Equals(['setUp', 'a', 'test', 'b', 'tearDown', 'c']))


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
