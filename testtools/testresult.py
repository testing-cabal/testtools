# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Test results and related things."""

__metaclass__ = type
__all__ = [
    'MultiTestResult',
    'TestResult',
    'ThreadsafeForwardingResult',
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


class ThreadsafeForwardingResult(TestResult):
    """A TestResult which ensures the target does not receive mixed up calls.
    
    This is used when receiving test results from multiple sources, and batches
    up all the activity for a single test into a thread-safe batch where all
    other ThreadsafeForwardingResult objects sharing the same semaphore will be
    locked out.

    Typical use of ThreadsafeForwardingResult involves creating one
    ThreadsafeForwardingResult per thread in a ConcurrentTestSuite. These
    forward to the TestResult that the ConcurrentTestSuite run method was
    called with.

    target.done() is called once for each ThreadsafeForwardingResult that
    forwards to the same target. If the target's done() takes special action,
    care should be taken to accommodate this.
    """

    def __init__(self, target, semaphore):
        """Create a ThreadsafeForwardingResult forwarding to target.

        :param target: A TestResult.
        :param semaphore: A threading.Semaphore with limit 1.
        """
        TestResult.__init__(self)
        self.result = target
        self.semaphore = semaphore

    def addError(self, test, err):
        self.semaphore.acquire()
        try:
            self.result.startTest(test)
            self.result.addError(test, err)
            self.result.stopTest(test)
        finally:
            self.semaphore.release()

    def addFailure(self, test, err):
        self.semaphore.acquire()
        try:
            self.result.startTest(test)
            self.result.addFailure(test, err)
            self.result.stopTest(test)
        finally:
            self.semaphore.release()

    def addSkip(self, test, reason):
        self.semaphore.acquire()
        try:
            self.result.startTest(test)
            self.result.addSkip(test, reason)
            self.result.stopTest(test)
        finally:
            self.semaphore.release()

    def addSuccess(self, test):
        self.semaphore.acquire()
        try:
            self.result.startTest(test)
            self.result.addSuccess(test)
            self.result.stopTest(test)
        finally:
            self.semaphore.release()

    def done(self):
        self.semaphore.acquire()
        try:
            self.result.done()
        finally:
            self.semaphore.release()
