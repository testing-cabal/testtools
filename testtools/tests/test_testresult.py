# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Test TestResults and related things."""

__metaclass__ = type

import datetime
import sys
import threading

from testtools import (
    ExtendedToOriginalDecorator,
    MultiTestResult,
    TestCase,
    TestResult,
    ThreadsafeForwardingResult,
    testresult,
    )
from testtools.content import Content, ContentType
from testtools.tests.helpers import (
    LoggingResult,
    Python26TestResult,
    Python27TestResult,
    ExtendedTestResult,
    )


class TestTestResultContract(TestCase):
    """Tests for the contract of TestResults."""

    def test_addExpectedFailure(self):
        # Calling addExpectedFailure(test, exc_info) completes ok.
        result = self.makeResult()
        result.addExpectedFailure(self, sys.exc_info())

    def test_addExpectedFailure_details(self):
        # Calling addExpectedFailure(test, details=xxx) completes ok.
        result = self.makeResult()
        result.addExpectedFailure(self, details={})

    def test_addError_details(self):
        # Calling addError(test, details=xxx) completes ok.
        result = self.makeResult()
        result.addError(self, details={})

    def test_addFailure_details(self):
        # Calling addFailure(test, details=xxx) completes ok.
        result = self.makeResult()
        result.addFailure(self, details={})

    def test_addSkipped(self):
        # Calling addSkip(test, reason) completes ok.
        result = self.makeResult()
        result.addSkip(self, u"Skipped for some reason")

    def test_addSkipped_details(self):
        # Calling addSkip(test, reason) completes ok.
        result = self.makeResult()
        result.addSkip(self, details={})

    def test_addUnexpectedSuccess(self):
        # Calling addUnexpectedSuccess(test) completes ok.
        result = self.makeResult()
        result.addUnexpectedSuccess(self)

    def test_addUnexpectedSuccess_details(self):
        # Calling addUnexpectedSuccess(test) completes ok.
        result = self.makeResult()
        result.addUnexpectedSuccess(self, details={})

    def test_addSuccess_details(self):
        # Calling addSuccess(test) completes ok.
        result = self.makeResult()
        result.addSuccess(self, details={})

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

    def test_now_datetime_now(self):
        result = self.makeResult()
        olddatetime = testresult.datetime
        def restore():
            testresult.datetime = olddatetime
        self.addCleanup(restore)
        class Module:
            pass
        now = datetime.datetime.now()
        stubdatetime = Module()
        stubdatetime.datetime = Module()
        stubdatetime.datetime.now = lambda:now
        testresult.datetime = stubdatetime
        self.assertEqual(now, result._now())
        # Set an explicit datetime, then go back to looking it up.
        result.time(datetime.datetime.now())
        self.assertNotEqual(now, result._now())
        result.time(None)
        self.assertEqual(now, result._now())

    def test_now_datetime_time(self):
        result = self.makeResult()
        now = datetime.datetime.now()
        result.time(now)
        self.assertEqual(now, result._now())


class TestWithFakeExceptions(TestCase):

    def makeExceptionInfo(self, exceptionFactory, *args, **kwargs):
        try:
            raise exceptionFactory(*args, **kwargs)
        except:
            return sys.exc_info()


class TestMultiTestResult(TestWithFakeExceptions):
    """Tests for `MultiTestResult`."""

    def setUp(self):
        TestWithFakeExceptions.setUp(self)
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
        TestWithFakeExceptions.setUp(self)
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


class TestExtendedToOriginalResultDecoratorBase(TestCase):

    def make_26_result(self):
        self.result = Python26TestResult()
        self.make_converter()

    def make_27_result(self):
        self.result = Python27TestResult()
        self.make_converter()

    def make_converter(self):
        self.converter = ExtendedToOriginalDecorator(self.result)

    def make_extended_result(self):
        self.result = ExtendedTestResult()
        self.make_converter()

    def check_outcome_details(self, outcome):
        """Call an outcome with a details dict to be passed through."""
        # This dict is /not/ convertible - thats deliberate, as it should
        # not hit the conversion code path.
        details = {'foo': 'bar'}
        getattr(self.converter, outcome)(self, details=details)
        self.assertEqual([(outcome, self, details)], self.result._events)

    def get_details_and_string(self):
        """Get a details dict and expected string."""
        text1 = lambda:["1\n2\n"]
        text2 = lambda:["3\n4\n"]
        bin1 = lambda:["5\n"]
        details = {'text 1': Content(ContentType('text', 'plain'), text1),
            'text 2': Content(ContentType('text', 'strange'), text2),
            'bin 1': Content(ContentType('application', 'binary'), bin1)}
        return (details, "Binary content: bin 1\n"
            "Text attachment: text 1\n------------\n1\n2\n"
            "------------\nText attachment: text 2\n------------\n"
            "3\n4\n------------\n")

    def check_outcome_details_to_exec_info(self, outcome, expected=None):
        """Call an outcome with a details dict to be made into exc_info."""
        # The conversion is a done using RemoteError and the string contents
        # of the text types in the details dict.
        if not expected:
            expected = outcome
        details, err_str = self.get_details_and_string()
        getattr(self.converter, outcome)(self, details=details)
        err = self.converter._details_to_exc_info(details)
        self.assertEqual([(expected, self, err)], self.result._events)

    def check_outcome_details_to_nothing(self, outcome, expected=None):
        """Call an outcome with a details dict to be swallowed."""
        if not expected:
            expected = outcome
        details = {'foo': 'bar'}
        getattr(self.converter, outcome)(self, details=details)
        self.assertEqual([(expected, self)], self.result._events)

    def check_outcome_details_to_string(self, outcome):
        """Call an outcome with a details dict to be stringified."""
        details, err_str = self.get_details_and_string()
        getattr(self.converter, outcome)(self, details=details)
        self.assertEqual([(outcome, self, err_str)], self.result._events)

    def check_outcome_exc_info(self, outcome, expected=None):
        """Check that calling a legacy outcome still works."""
        # calling some outcome with the legacy exc_info style api (no keyword
        # parameters) gets passed through.
        if not expected:
            expected = outcome
        err = sys.exc_info()
        getattr(self.converter, outcome)(self, err)
        self.assertEqual([(expected, self, err)], self.result._events)

    def check_outcome_exc_info_to_nothing(self, outcome, expected=None):
        """Check that calling a legacy outcome on a fallback works."""
        # calling some outcome with the legacy exc_info style api (no keyword
        # parameters) gets passed through.
        if not expected:
            expected = outcome
        err = sys.exc_info()
        getattr(self.converter, outcome)(self, err)
        self.assertEqual([(expected, self)], self.result._events)

    def check_outcome_nothing(self, outcome, expected=None):
        """Check that calling a legacy outcome still works."""
        if not expected:
            expected = outcome
        getattr(self.converter, outcome)(self)
        self.assertEqual([(expected, self)], self.result._events)

    def check_outcome_string_nothing(self, outcome, expected):
        """Check that calling outcome with a string calls expected."""
        getattr(self.converter, outcome)(self, "foo")
        self.assertEqual([(expected, self)], self.result._events)

    def check_outcome_string(self, outcome):
        """Check that calling outcome with a string works."""
        getattr(self.converter, outcome)(self, "foo")
        self.assertEqual([(outcome, self, "foo")], self.result._events)


class TestExtendedToOriginalResultDecorator(
    TestExtendedToOriginalResultDecoratorBase):

    def test_progress_py26(self):
        self.make_26_result()
        self.converter.progress(1, 2)

    def test_progress_py27(self):
        self.make_27_result()
        self.converter.progress(1, 2)

    def test_progress_pyextended(self):
        self.make_extended_result()
        self.converter.progress(1, 2)
        self.assertEqual([('progress', 1, 2)], self.result._events)

    def test_shouldStop(self):
        self.make_26_result()
        self.assertEqual(False, self.converter.shouldStop)
        self.converter.decorated.stop()
        self.assertEqual(True, self.converter.shouldStop)

    def test_startTest_py26(self):
        self.make_26_result()
        self.converter.startTest(self)
        self.assertEqual([('startTest', self)], self.result._events)
    
    def test_startTest_py27(self):
        self.make_27_result()
        self.converter.startTest(self)
        self.assertEqual([('startTest', self)], self.result._events)

    def test_startTest_pyextended(self):
        self.make_extended_result()
        self.converter.startTest(self)
        self.assertEqual([('startTest', self)], self.result._events)

    def test_startTestRun_py26(self):
        self.make_26_result()
        self.converter.startTestRun()
        self.assertEqual([], self.result._events)
    
    def test_startTestRun_py27(self):
        self.make_27_result()
        self.converter.startTestRun()
        self.assertEqual([('startTestRun',)], self.result._events)

    def test_startTestRun_pyextended(self):
        self.make_extended_result()
        self.converter.startTestRun()
        self.assertEqual([('startTestRun',)], self.result._events)

    def test_stopTest_py26(self):
        self.make_26_result()
        self.converter.stopTest(self)
        self.assertEqual([('stopTest', self)], self.result._events)
    
    def test_stopTest_py27(self):
        self.make_27_result()
        self.converter.stopTest(self)
        self.assertEqual([('stopTest', self)], self.result._events)

    def test_stopTest_pyextended(self):
        self.make_extended_result()
        self.converter.stopTest(self)
        self.assertEqual([('stopTest', self)], self.result._events)

    def test_stopTestRun_py26(self):
        self.make_26_result()
        self.converter.stopTestRun()
        self.assertEqual([], self.result._events)
    
    def test_stopTestRun_py27(self):
        self.make_27_result()
        self.converter.stopTestRun()
        self.assertEqual([('stopTestRun',)], self.result._events)

    def test_stopTestRun_pyextended(self):
        self.make_extended_result()
        self.converter.stopTestRun()
        self.assertEqual([('stopTestRun',)], self.result._events)

    def test_tags_py26(self):
        self.make_26_result()
        self.converter.tags(1, 2)

    def test_tags_py27(self):
        self.make_27_result()
        self.converter.tags(1, 2)

    def test_tags_pyextended(self):
        self.make_extended_result()
        self.converter.tags(1, 2)
        self.assertEqual([('tags', 1, 2)], self.result._events)

    def test_time_py26(self):
        self.make_26_result()
        self.converter.time(1)

    def test_time_py27(self):
        self.make_27_result()
        self.converter.time(1)

    def test_time_pyextended(self):
        self.make_extended_result()
        self.converter.time(1)
        self.assertEqual([('time', 1)], self.result._events)


class TestExtendedToOriginalAddError(TestExtendedToOriginalResultDecoratorBase):

    outcome = 'addError'

    def test_outcome_Original_py26(self):
        self.make_26_result()
        self.check_outcome_exc_info(self.outcome)
    
    def test_outcome_Original_py27(self):
        self.make_27_result()
        self.check_outcome_exc_info(self.outcome)

    def test_outcome_Original_pyextended(self):
        self.make_extended_result()
        self.check_outcome_exc_info(self.outcome)

    def test_outcome_Extended_py26(self):
        self.make_26_result()
        self.check_outcome_details_to_exec_info(self.outcome)
    
    def test_outcome_Extended_py27(self):
        self.make_27_result()
        self.check_outcome_details_to_exec_info(self.outcome)

    def test_outcome_Extended_pyextended(self):
        self.make_extended_result()
        self.check_outcome_details(self.outcome)

    def test_outcome__no_details(self):
        self.make_extended_result()
        self.assertRaises(ValueError,
            getattr(self.converter, self.outcome), self)


class TestExtendedToOriginalAddFailure(
    TestExtendedToOriginalAddError):

    outcome = 'addFailure'


class TestExtendedToOriginalAddExpectedFailure(
    TestExtendedToOriginalAddError):

    outcome = 'addExpectedFailure'

    def test_outcome_Original_py26(self):
        self.make_26_result()
        self.check_outcome_exc_info_to_nothing(self.outcome, 'addSuccess')
    
    def test_outcome_Extended_py26(self):
        self.make_26_result()
        self.check_outcome_details_to_nothing(self.outcome, 'addSuccess')
    


class TestExtendedToOriginalAddSkip(
    TestExtendedToOriginalResultDecoratorBase):

    outcome = 'addSkip'

    def test_outcome_Original_py26(self):
        self.make_26_result()
        self.check_outcome_string_nothing(self.outcome, 'addSuccess')
    
    def test_outcome_Original_py27(self):
        self.make_27_result()
        self.check_outcome_string(self.outcome)

    def test_outcome_Original_pyextended(self):
        self.make_extended_result()
        self.check_outcome_string(self.outcome)

    def test_outcome_Extended_py26(self):
        self.make_26_result()
        self.check_outcome_string_nothing(self.outcome, 'addSuccess')
    
    def test_outcome_Extended_py27(self):
        self.make_27_result()
        self.check_outcome_details_to_string(self.outcome)

    def test_outcome_Extended_pyextended(self):
        self.make_extended_result()
        self.check_outcome_details(self.outcome)

    def test_outcome__no_details(self):
        self.make_extended_result()
        self.assertRaises(ValueError,
            getattr(self.converter, self.outcome), self)


class TestExtendedToOriginalAddSuccess(
    TestExtendedToOriginalResultDecoratorBase):

    outcome = 'addSuccess'
    expected = 'addSuccess'

    def test_outcome_Original_py26(self):
        self.make_26_result()
        self.check_outcome_nothing(self.outcome, self.expected)
    
    def test_outcome_Original_py27(self):
        self.make_27_result()
        self.check_outcome_nothing(self.outcome)

    def test_outcome_Original_pyextended(self):
        self.make_extended_result()
        self.check_outcome_nothing(self.outcome)

    def test_outcome_Extended_py26(self):
        self.make_26_result()
        self.check_outcome_details_to_nothing(self.outcome, self.expected)
    
    def test_outcome_Extended_py27(self):
        self.make_27_result()
        self.check_outcome_details_to_nothing(self.outcome)

    def test_outcome_Extended_pyextended(self):
        self.make_extended_result()
        self.check_outcome_details(self.outcome)


class TestExtendedToOriginalAddUnexpectedSuccess(
    TestExtendedToOriginalAddSuccess):

    outcome = 'addUnexpectedSuccess'


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
