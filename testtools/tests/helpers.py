# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Helpers for tests."""

import sys

__metaclass__ = type
__all__ = [
    'LoggingResult',
    ]

from testtools import TestResult


try:
    raise Exception
except Exception:
    an_exc_info = sys.exc_info()

# Deprecated: This classes attributes are somewhat non deterministic which
# leads to hard to predict tests (because Python upstream are changing things.
class LoggingResult(TestResult):
    """TestResult that logs its event to a list."""

    def __init__(self, log):
        self._events = log
        super(LoggingResult, self).__init__()

    def startTest(self, test):
        self._events.append(('startTest', test))
        super(LoggingResult, self).startTest(test)

    def stopTest(self, test):
        self._events.append(('stopTest', test))
        super(LoggingResult, self).stopTest(test)

    def addFailure(self, test, error):
        self._events.append(('addFailure', test, error))
        super(LoggingResult, self).addFailure(test, error)

    def addError(self, test, error):
        self._events.append(('addError', test, error))
        super(LoggingResult, self).addError(test, error)

    def addSkip(self, test, reason):
        self._events.append(('addSkip', test, reason))
        super(LoggingResult, self).addSkip(test, reason)

    def addSuccess(self, test):
        self._events.append(('addSuccess', test))
        super(LoggingResult, self).addSuccess(test)

    def startTestRun(self):
        self._events.append('startTestRun')
        super(LoggingResult, self).startTestRun()
        
    def stopTestRun(self):
        self._events.append('stopTestRun')
        super(LoggingResult, self).stopTestRun()
        
    def done(self):
        self._events.append('done')
        super(LoggingResult, self).done()


class LoggingBase(object):
    """Basic support for logging of results."""
    
    def __init__(self):
        self._events = []
        self.shouldStop = False


# Note, the following three classes are different to LoggingResult by
# being fully defined exact matches rather than supersets.
class Python26TestResult(LoggingBase):
    """A precisely python 2.6 like test result, that logs."""

    def addError(self, test, err):
        self._events.append(('addError', test, err))

    def addFailure(self, test, err):
        self._events.append(('addFailure', test, err))

    def addSuccess(self, test):
        self._events.append(('addSuccess', test))

    def startTest(self, test):
        self._events.append(('startTest', test))

    def stop(self):
        self.shouldStop = True

    def stopTest(self, test):
        self._events.append(('stopTest', test))


class Python27TestResult(Python26TestResult):
    """A precisely python 2.7 like test result, that logs."""

    def addExpectedFailure(self, test, err):
        self._events.append(('addExpectedFailure', test, err))

    def addSkip(self, test, reason):
        self._events.append(('addSkip', test, reason))

    def addUnexpectedSuccess(self, test):
        self._events.append(('addUnexpectedSuccess', test))

    def startTestRun(self):
        self._events.append(('startTestRun',))

    def stopTestRun(self):
        self._events.append(('stopTestRun',))


class ExtendedTestResult(Python27TestResult):
    """A test result like the proposed extended unittest result API."""

    def addError(self, test, err=None, details=None):
        self._events.append(('addError', test, err or details))

    def addFailure(self, test, err=None, details=None):
        self._events.append(('addFailure', test, err or details))

    def addExpectedFailure(self, test, err=None, details=None):
        self._events.append(('addExpectedFailure', test, err or details))

    def addSkip(self, test, reason=None, details=None):
        self._events.append(('addSkip', test, reason or details))

    def addSuccess(self, test, details=None):
        if details:
            self._events.append(('addSuccess', test, details))
        else:
            self._events.append(('addSuccess', test))

    def addUnexpectedSuccess(self, test, details=None):
        if details is not None:
            self._events.append(('addUnexpectedSuccess', test, details))
        else:
            self._events.append(('addUnexpectedSuccess', test))

    def progress(self, offset, whence):
        self._events.append(('progress', offset, whence))

    def tags(self, new_tags, gone_tags):
        self._events.append(('tags', new_tags, gone_tags))

    def time(self, time):
        self._events.append(('time', time))
