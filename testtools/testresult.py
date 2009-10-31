# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Test results and related things."""

__metaclass__ = type
__all__ = [
    'ExtendedToOriginalDecorator',
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
        # -- Start: As per python 2.7 --
        self.expectedFailures = []
        self.unexpectedSuccesses = []
        # -- End:   As per python 2.7 --

    def addExpectedFailure(self, test, err):
        """Called when a test has failed in an expected manner.

        Like with addSuccess and addError, testStopped should still be called.

        :param test: The test that has been skipped.
        :param err: The exc_info of the error that was raised.
        :return: None
        """
        # This is the python 2.7 implementation
        self.expectedFailures.append(
            (test, self._exc_info_to_string(err, test)))

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

    def addUnexpectedSuccess(self, test):
        """Called when a test was expected to fail, but succeed."""
        self.unexpectedSuccesses.append(test)

    def startTestRun(self):
        """Called before a test run starts.

        New in python 2.7
        """

    def stopTestRun(self):
        """Called after a test run completes

        New in python 2.7
        """

    def done(self):
        """Called when the test runner is done.
        
        deprecated in favour of stopTestRun.
        """


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

    def addExpectedFailure(self, test, err):
        self._dispatch('addExpectedFailure', test, err)

    def addFailure(self, test, failure):
        self._dispatch('addFailure', test, failure)

    def addSkip(self, test, reason):
        self._dispatch('addSkip', test, reason)

    def addSuccess(self, test):
        self._dispatch('addSuccess', test)

    def addUnexpectedSuccess(self, test):
        self._dispatch('addUnexpectedSuccess', test)

    def startTestRun(self):
        self._dispatch('startTestRun')

    def stopTestRun(self):
        self._dispatch('stopTestRun')

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

    def addExpectedFailure(self, test, err):
        self.semaphore.acquire()
        try:
            self.result.startTest(test)
            self.result.addExpectedFailure(test, err)
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

    def addUnexpectedSuccess(self, test):
        self.semaphore.acquire()
        try:
            self.result.startTest(test)
            self.result.addUnexpectedSuccess(test)
            self.result.stopTest(test)
        finally:
            self.semaphore.release()

    def startTestRun(self):
        self.semaphore.acquire()
        try:
            self.result.startTestRun()
        finally:
            self.semaphore.release()

    def stopTestRun(self):
        self.semaphore.acquire()
        try:
            self.result.stopTestRun()
        finally:
            self.semaphore.release()

    def done(self):
        self.semaphore.acquire()
        try:
            self.result.done()
        finally:
            self.semaphore.release()


class ExtendedToOriginalDecorator(object):
    """Permit new TestResult API code to degrade gracefully with old results.

    This decorates an existing TestResult and converts missing outcomes
    such as addSkip to older outcomes such as addSuccess. It also supports
    the extended details protocol. In all cases the most recent protocol
    is attempted first, and fallbacks only occur when the decorated result
    does not support the newer style of calling.
    """

    def __init__(self, decorated):
        self.decorated = decorated

    def addError(self, test, err=None, details=None):
        self._check_args(err, details)
        if details is not None:
            try:
                return self.decorated.addError(test, details=details)
            except TypeError, e:
                # have to convert
                err = self._details_to_exc_info(details)
        return self.decorated.addError(test, err)

    def addExpectedFailure(self, test, err=None, details=None):
        self._check_args(err, details)
        addExpectedFailure = getattr(self.decorated, 'addExpectedFailure', None)
        if addExpectedFailure is None:
            return self.addSuccess(test)
        if details is not None:
            try:
                return addExpectedFailure(test, details=details)
            except TypeError, e:
                # have to convert
                err = self._details_to_exc_info(details)
        return addExpectedFailure(test, err)

    def addFailure(self, test, err=None, details=None):
        self._check_args(err, details)
        if details is not None:
            try:
                return self.decorated.addFailure(test, details=details)
            except TypeError, e:
                # have to convert
                err = self._details_to_exc_info(details)
        return self.decorated.addFailure(test, err)

    def addSkip(self, test, reason=None, details=None):
        self._check_args(reason, details)
        addSkip = getattr(self.decorated, 'addSkip', None)
        if addSkip is None:
            return self.decorated.addSuccess(test)
        if details is not None:
            try:
                return addSkip(test, details=details)
            except TypeError, e:
                # have to convert
                reason = self._details_to_str(details)
        return addSkip(test, reason)

    def addUnexpectedSuccess(self, test, details=None):
        outcome = getattr(self.decorated, 'addUnexpectedSuccess', None)
        if outcome is None:
            return self.decorated.addSuccess(test)
        if details is not None:
            try:
                return outcome(test, details=details)
            except TypeError, e:
                pass
        return outcome(test)

    def addSuccess(self, test, details=None):
        if details is not None:
            try:
                return self.decorated.addSuccess(test, details=details)
            except TypeError, e:
                pass
        return self.decorated.addSuccess(test)

    def _check_args(self, err, details):
        param_count = 0
        if err is not None:
            param_count += 1
        if details is not None:
            param_count += 1
        if param_count != 1:
            raise ValueError("Must pass only one of err '%s' and details '%s"
                % (err, details))

    def _details_to_exc_info(self, details):
        """Convert a details dict to an exc_info tuple."""
        return (_StringException,
            _StringException(self._details_to_str(details)), None)

    def _details_to_str(self, details):
        """Convert a details dict to a string."""
        lines = []
        # sorted is for testing, may want to remove that and use a dict
        # subclass with defined order for iteritems instead.
        for key, content in sorted(details.iteritems()):
            if content.content_type.type != 'text':
                lines.append('Binary content: %s\n' % key)
                continue
            lines.append('Text attachment: %s\n' % key)
            lines.append('------------\n')
            lines.extend(content.iter_bytes())
            if not lines[-1].endswith('\n'):
                lines.append('\n')
            lines.append('------------\n')
        return ''.join(lines)

    def progress(self, offset, whence):
        method = getattr(self.decorated, 'progress', None)
        if method is None:
            return
        return method(offset, whence)

    @property
    def shouldStop(self):
        return self.decorated.shouldStop

    def startTest(self, test):
        return self.decorated.startTest(test)

    def startTestRun(self):
        try:
            return self.decorated.startTestRun()
        except AttributeError:
            return

    def stop(self):
        return self.decorated.stop()

    def stopTest(self, test):
        return self.decorated.stopTest(test)

    def stopTestRun(self):
        try:
            return self.decorated.stopTestRun()
        except AttributeError:
            return

    def tags(self, new_tags, gone_tags):
        method = getattr(self.decorated, 'tags', None)
        if method is None:
            return
        return method(new_tags, gone_tags)

    def time(self, a_datetime):
        method = getattr(self.decorated, 'time', None)
        if method is None:
            return
        return method(a_datetime)

    def wasSuccessful(self):
        return self.decorated.wasSuccessful()


class _StringException(Exception):
    """An exception made from an arbitrary string."""

    def __eq__(self, other):
        try:
            return self.args == other.args
        except AttributeError:
            return False

