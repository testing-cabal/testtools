# Copyright (c) 2010 Jonathan M. Lange. See LICENSE for details.

"""Tests for the DeferredRunTest single test execution logic."""

from testtools import (
    TestCase,
    )
from testtools.deferredruntest import (
    AsynchronousDeferredRunTest,
    SynchronousDeferredRunTest,
    )
from testtools.tests.helpers import ExtendedTestResult
from testtools.matchers import Equals

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

    def test_setUp_returns_deferred_that_fires_later(self):
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

    def test_calls_setUp_test_tearDown_in_sequence(self):
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
        # XXX: We aren't actually firing the Deferred's yet, so this test
        # ought to hang.

        # XXX: We ought to have some kind of timeout for the test case to
        # handle the times when a Deferred is returned that never fires.

        # XXX: Somehow the reactor ought to be passed into the runner. Perhaps
        # the clock should be separate. Not sure.

        # XXX: We ought to catch unhandled errors in Deferreds.  This means
        # hooking into Twisted's logging system.
        self.assertThat(
            call_log, Equals(['setUp', 'a', 'test', 'b', 'tearDown', 'c']))


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
