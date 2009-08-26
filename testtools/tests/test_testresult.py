# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Test TestResults and related things."""

__metaclass__ = type

import sys
import threading

from testtools import (
    MultiTestResult,
    TestCase,
    TestResult,
    ThreadsafeForwardingResult,
    )
from testtools.tests.helpers import LoggingResult


class TestTestResultContract(TestCase):
    """Tests for the contract of TestResults."""

    def test_addSkipped(self):
        # Calling addSkip(test, reason) completes ok.
        result = self.makeResult()
        result.addSkip(self, u"Skipped for some reason")

    def test_startStopTestRun(self):
        # Calling startTestRun completes ok.
        result = self.makeResult()
        result.startTestRun()
        result.stopTestRun()


class TestTestResultContract(TestTestResultContract):

    def makeResult(self):
        return TestResult()


class TestMultiTestresultContract(TestTestResultContract):

    def makeResult(self):
        return MultiTestResult(TestResult(), TestResult())


class TestThreadSafeForwardingResultContract(TestTestResultContract):

    def makeResult(self):
        result_semaphore = threading.Semaphore(1)
        target = TestResult()
        return ThreadsafeForwardingResult(target, result_semaphore)


class TestTestResult(TestCase):
    """Tests for `TestResult`."""

    def makeResult(self):
        """Make an arbitrary result for testing."""
        return TestResult()

    def test_addSkipped(self):
        # Calling addSkip on a TestResult records the test that was skipped in
        # its skip_reasons dict.
        result = self.makeResult()
        result.addSkip(self, u"Skipped for some reason")
        self.assertEqual({u"Skipped for some reason":[self]},
            result.skip_reasons)
        result.addSkip(self, u"Skipped for some reason")
        self.assertEqual({u"Skipped for some reason":[self, self]},
            result.skip_reasons)
        result.addSkip(self, u"Skipped for another reason")
        self.assertEqual({u"Skipped for some reason":[self, self],
            u"Skipped for another reason":[self]},
            result.skip_reasons)

    def test_done(self):
        # `TestResult` has a `done` method that, by default, does nothing.
        self.makeResult().done()


class TestWithFakeExceptions(TestCase):

    def makeExceptionInfo(self, exceptionFactory, *args, **kwargs):
        try:
            raise exceptionFactory(*args, **kwargs)
        except:
            return sys.exc_info()


class TestMultiTestResult(TestWithFakeExceptions):
    """Tests for `MultiTestResult`."""

    def setUp(self):
        self.result1 = LoggingResult([])
        self.result2 = LoggingResult([])
        self.multiResult = MultiTestResult(self.result1, self.result2)

    def assertResultLogsEqual(self, expectedEvents):
        """Assert that our test results have received the expected events."""
        self.assertEqual(expectedEvents, self.result1._events)
        self.assertEqual(expectedEvents, self.result2._events)

    def test_empty(self):
        # Initializing a `MultiTestResult` doesn't do anything to its
        # `TestResult`s.
        self.assertResultLogsEqual([])

    def test_startTest(self):
        # Calling `startTest` on a `MultiTestResult` calls `startTest` on all
        # its `TestResult`s.
        self.multiResult.startTest(self)
        self.assertResultLogsEqual([('startTest', self)])

    def test_stopTest(self):
        # Calling `stopTest` on a `MultiTestResult` calls `stopTest` on all
        # its `TestResult`s.
        self.multiResult.stopTest(self)
        self.assertResultLogsEqual([('stopTest', self)])

    def test_addSkipped(self):
        # Calling `addSkip` on a `MultiTestResult` calls addSkip on its
        # results.
        reason = u"Skipped for some reason"
        self.multiResult.addSkip(self, reason)
        self.assertResultLogsEqual([('addSkip', self, reason)])

    def test_addSuccess(self):
        # Calling `addSuccess` on a `MultiTestResult` calls `addSuccess` on
        # all its `TestResult`s.
        self.multiResult.addSuccess(self)
        self.assertResultLogsEqual([('addSuccess', self)])

    def test_done(self):
        # Calling `done` on a `MultiTestResult` calls `done` on all its
        # `TestResult`s.
        self.multiResult.done()
        self.assertResultLogsEqual([('done')])

    def test_addFailure(self):
        # Calling `addFailure` on a `MultiTestResult` calls `addFailure` on
        # all its `TestResult`s.
        exc_info = self.makeExceptionInfo(AssertionError, 'failure')
        self.multiResult.addFailure(self, exc_info)
        self.assertResultLogsEqual([('addFailure', self, exc_info)])

    def test_addError(self):
        # Calling `addError` on a `MultiTestResult` calls `addError` on all
        # its `TestResult`s.
        exc_info = self.makeExceptionInfo(RuntimeError, 'error')
        self.multiResult.addError(self, exc_info)
        self.assertResultLogsEqual([('addError', self, exc_info)])

    def test_startTestRun(self):
        # Calling `startTestRun` on a `MultiTestResult` forwards to all its
        # `TestResult`s.
        self.multiResult.startTestRun()
        self.assertResultLogsEqual([('startTestRun')])

    def test_stopTestRun(self):
        # Calling `stopTestRun` on a `MultiTestResult` forwards to all its
        # `TestResult`s.
        self.multiResult.stopTestRun()
        self.assertResultLogsEqual([('stopTestRun')])


class TestThreadSafeForwardingResult(TestWithFakeExceptions):
    """Tests for `MultiTestResult`."""

    def setUp(self):
        self.result_semaphore = threading.Semaphore(1)
        self.target = LoggingResult([])
        self.result1 = ThreadsafeForwardingResult(self.target,
            self.result_semaphore)

    def test_nonforwarding_methods(self):
        # startTest and stopTest are not forwarded because they need to be
        # batched.
        self.result1.startTest(self)
        self.result1.stopTest(self)
        self.assertEqual([], self.target._events)

    def test_startTestRun(self):
        self.result1.startTestRun()
        self.result2 = ThreadsafeForwardingResult(self.target,
            self.result_semaphore)
        self.result2.startTestRun()
        self.assertEqual(["startTestRun", "startTestRun"], self.target._events)

    def test_stopTestRun(self):
        self.result1.stopTestRun()
        self.result2 = ThreadsafeForwardingResult(self.target,
            self.result_semaphore)
        self.result2.stopTestRun()
        self.assertEqual(["stopTestRun", "stopTestRun"], self.target._events)

    def test_done(self):
        self.result1.done()
        self.result2 = ThreadsafeForwardingResult(self.target,
            self.result_semaphore)
        self.result2.done()
        self.assertEqual(["done", "done"], self.target._events)

    def test_forwarding_methods(self):
        # error, failure, skip and success are forwarded in batches.
        exc_info1 = self.makeExceptionInfo(RuntimeError, 'error')
        self.result1.addError(self, exc_info1)
        exc_info2 = self.makeExceptionInfo(AssertionError, 'failure')
        self.result1.addFailure(self, exc_info2)
        reason = u"Skipped for some reason"
        self.result1.addSkip(self, reason)
        self.result1.addSuccess(self)
        self.assertEqual([('startTest', self),
            ('addError', self, exc_info1),
            ('stopTest', self),
            ('startTest', self),
            ('addFailure', self, exc_info2),
            ('stopTest', self),
            ('startTest', self),
            ('addSkip', self, reason),
            ('stopTest', self),
            ('startTest', self),
            ('addSuccess', self),
            ('stopTest', self),
            ], self.target._events)


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
