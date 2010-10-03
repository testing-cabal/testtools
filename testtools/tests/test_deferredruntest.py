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

    def make_result(self):
        return ExtendedTestResult()

    def make_runner(self, test):
        return AsynchronousDeferredRunTest(test, test.exception_handlers)

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
        test = SomeCase('test_success')
        runner = self.make_runner(test)
        result = self.make_result()
        runner.run(result)
        # XXX: We aren't actually firing the Deferred's yet, so this test
        # ought to hang.

        # XXX: We ought to have some kind of timeout for the test case to
        # handle the times when a Deferred is returned that never fires.

        # XXX: Somehow the reactor ought to be passed into the runner. Perhaps
        # the clock should be separate. Not sure.

        # XXX: We ought to catch unhandled errors in Deferreds.  This means
        # hooking into Twisted's logging system.
        self.assertThat(call_log, Equals(['setUp', 'test', 'tearDown']))


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
