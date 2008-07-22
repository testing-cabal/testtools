# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Test TestResults and related things."""

__metaclass__ = type

from pyunit3k import ITestResult, TestCase, TestResult


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


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
