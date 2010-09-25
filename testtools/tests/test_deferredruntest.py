# Copyright (c) 2010 Jonathan M. Lange. See LICENSE for details.

"""Tests for the DeferredRunTest single test execution logic."""

from testtools import (
    TestCase,
    )
from testtools.deferredruntest import DeferredRunTest
from testtools.tests.helpers import ExtendedTestResult
from testtools.matchers import Equals

from twisted.internet import defer


class TestDeferredRunTest(TestCase):

    def test_synchronous_success(self):
        class SomeCase(TestCase):
            def test_success(self):
                return defer.succeed(None)
        test = SomeCase('test_success')
        runner = DeferredRunTest(test)
        result = ExtendedTestResult()
        runner.run(result)
        self.assertThat(
            result._events, Equals([
                ('startTest', test),
                ('addSuccess', test),
                ('stopTest', test)]))

    def test_synchronous_failure(self):
        class SomeCase(TestCase):
            def test_failure(self):
                return defer.maybeDeferred(self.fail, "Egads!")
        test = SomeCase('test_failure')
        runner = DeferredRunTest(test, test.exception_handlers)
        result = ExtendedTestResult()
        runner.run(result)
        self.assertThat(
            [event[:2] for event in result._events], Equals([
                ('startTest', test),
                ('addFailure', test),
                ('stopTest', test)]))



def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
