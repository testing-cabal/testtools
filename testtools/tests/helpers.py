# Copyright (c) 2008-2011 testtools developers. See LICENSE for details.

"""Helpers for tests."""

__all__ = [
    'LoggingResult',
    ]

import sys

from fixtures import Fixture

from testtools import TestResult
from testtools.helpers import try_import
from testtools import runtest


# GZ 2010-08-12: Don't do this, pointlessly creates an exc_info cycle
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

    def time(self, a_datetime):
        self._events.append(('time', a_datetime))
        super(LoggingResult, self).time(a_datetime)


def safe_hasattr(obj, attr):
    marker = object()
    return getattr(obj, attr, marker) is not marker


def is_stack_hidden():
    return safe_hasattr(runtest, '__unittest')


def hide_testtools_stack(should_hide=True):
    modules = [
        'testtools.matchers',
        'testtools.runtest',
        'testtools.testcase',
        ]
    for module_name in modules:
        module = try_import(module_name)
        if should_hide:
            setattr(module, '__unittest', True)
        else:
            try:
                delattr(module, '__unittest')
            except AttributeError:
                # Attribute already doesn't exist. Our work here is done.
                pass


class StackHidingFixture(Fixture):

    def __init__(self, should_hide):
        super(StackHidingFixture, self).__init__()
        self._should_hide = should_hide

    def setUp(self):
        super(StackHidingFixture, self).setUp()
        self.addCleanup(hide_testtools_stack, is_stack_hidden())
        hide_testtools_stack(self._should_hide)
