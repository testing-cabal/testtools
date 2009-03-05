# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Test results and related things."""

__metaclass__ = type
__all__ = [
    'MultiTestResult',
    'TestResult',
    ]

import unittest


class TestResult(unittest.TestResult):
    """Subclass of unittest.TestResult extending the protocol for flexability.

    :ivar skip_reasons: A dict of skip-reasons -> list of tests. See addSkip.
    """

    def __init__(self):
        super(TestResult, self).__init__()
        self.skip_reasons = {}

    def addSkip(self, test, reason):
        """Called when a test has been skipped rather than running.

        Like with addSuccess and addError, testStopped should still be called.

        This must be called by the TestCase. 'addError' and 'addFailure' will
        not call addSkip, since they have no assumptions about the kind of
        errors that a test can raise.

        :param test: The test that has been skipped.
        :param reason: The reason for the test being skipped. For instance,
            u"pyGL is not available".
        :return: None
        """
        skip_list = self.skip_reasons.setdefault(reason, [])
        skip_list.append(test)

    def done(self):
        """Called when the test runner is done."""


class MultiTestResult(TestResult):
    """A test result that dispatches to many test results."""

    def __init__(self, *results):
        TestResult.__init__(self)
        self._results = list(results)

    def _dispatch(self, message, *args, **kwargs):
        for result in self._results:
            getattr(result, message)(*args, **kwargs)

    def startTest(self, test):
        self._dispatch('startTest', test)

    def stopTest(self, test):
        self._dispatch('stopTest', test)

    def addError(self, test, error):
        self._dispatch('addError', test, error)

    def addFailure(self, test, failure):
        self._dispatch('addFailure', test, failure)

    def addSkip(self, test, reason):
        self._dispatch('addSkip', test, reason)

    def addSuccess(self, test):
        self._dispatch('addSuccess', test)

    def done(self):
        self._dispatch('done')
