# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Test TestResults and related things."""

__metaclass__ = type

from pyunit3k import ITestResult, MultiTestResult, TestCase, TestResult
from pyunit3k.tests.helpers import LoggingResult


class TestTestResult(TestCase):
    """Tests for `TestResult`."""

    def makeResult(self):
        """Make an arbitrary result for testing."""
        return TestResult()

    def test_done(self):
        # `TestResult` has a `done` method that, by default, does nothing.
        self.makeResult().done()

    def test_interface(self):
        # pyunit3k's `TestResult` implements `ITestResult`.
        self.assertTrue(
            ITestResult.providedBy(self.makeResult()),
            'ITestResult not provided by TestResult')


class TestMultiTestResult(TestCase):
    """Tests for `MultiTestResult`."""

    def setUp(self):
        self.result1 = LoggingResult([])
        self.result2 = LoggingResult([])
        self.multiResult = MultiTestResult(self.result1, self.result2)

    def test_empty(self):
        # Initializing a `MultiTestResult` doesn't do anything to its
        # `TestResult`s.
        self.assertEqual([], self.result1._events)
        self.assertEqual([], self.result2._events)

    def test_startTest(self):
        # Calling `startTest` on a `MultiTestResult` calls `startTest` on all
        # its `TestResult`s.
        self.multiResult.startTest(self)
        self.assertEqual([('startTest', self)], self.result1._events)
        self.assertEqual([('startTest', self)], self.result2._events)


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
