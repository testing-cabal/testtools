# Copyright (c) 2015 testtools developers. See LICENSE for details.
"""Interfaces used within testtools."""

from zope.interface import Attribute, Interface


class IRunnable(Interface):
    """A thing that a test runner can run."""

    def __call__(result=None):
        """Equivalent to ``run``."""

    def countTestCases():
        """Return the number of tests this represents."""

    def debug():
        pass

    def run(result=None):
        """Run the test."""


class ITestSuite(IRunnable):
    """A suite of tests."""

    def __iter__():
        """Iterate over the IRunnables in suite."""


class ITestCase(IRunnable):
    """An individual test case."""

    def __str__():
        """Return a short, human-readable description."""

    def id():
        """A unique identifier."""

    def shortDescription(self):
        """Return a short, human-readable description."""


class IExceptionHandler(Interface):
    """Handle an exception from user code."""

    def __call__(test_case, test_result, exception_value):
        """Handle an exception raised from user code.

        :param TestCase test_case: The test that raised the exception.
        :param TestResult test_result: Where to report the result to.
        :param Exception exception_value: The raised exception.
        """


class IRunTestFactory(Interface):
    """Create a ``RunTest`` object."""

    def __call__(test_case, exception_handlers, last_resort=None):
        """Construct and return a ``RunTest``.

        :param ITestCase+ITestCaseStrategy test_case: The test case to run.
        :param exception_handlers: List of (exception_type, IExceptionHandler).
            This list can be mutated any time.
        :param IExceptionHandler last_resort: exception handler to be used as
            a last resort.

        :return: An ``IRunTest``.
        """


class IRunTest(Interface):
    """Called from inside ITestCase.run to actually run the test."""

    # XXX: jml thinks this ought to be run(case, result), and IRunTestFactory
    # shouldn't take a test_case at all.
    def run(result):
        """Run the test."""


# TODO:
# - legacy test result interfaces
# - document which test result interfaces are expected above
# - stream result interface
# - make TestControl an interface, use it by composition in
#   ExtendedToOriginalDecorator
# - figure out whether .errors, .skip_reasons, .failures, etc. should be
#   on IExtendedTestResult or on a separate interface that TestResult also
#   implements
# - figure out what to do about failfast and tb_locals
# - interface for TagContext?
# - failureException?
# - loading stuff, e.g. test_suite, load_tests?

class ITestCaseStrategy(ITestCase):
    """What ``RunTest`` needs to run a test case.

    This is a test that has a ``setUp``, a test body, and a ``tearDown``.

    Must also be an ``ITestCase`` so the results can be reported.
    """

    """Should local variables be captured in tracebacks?

    Can be mutated externally.
    """
    __testtools_tb_locals__ = Attribute('__testtools_tb_locals__')

    """List of ``(function, args, kwargs)`` called in reverse order after test.

    This list is mutated by ``RunTest``.
    """
    _cleanups = Attribute('_cleanups')

    """If non-False, then force the test to fail regardless of behavior.

    If not defined, assumed to be False.
    """
    force_failure = Attribute('force_failure')

    def defaultTestResult():
        """Construct a test result object for reporting results."""

    def _get_test_method():
        """Get the test method we are exercising."""

    def _run_setup(result):
        """Run the ``setUp`` method of the test."""

    def _run_test_method(result):
        """Run the test method.

        Must run the method returned by _get_test_method.
        """

    def _run_teardown(result):
        """Run the ``tearDown`` method of the test."""

    def getDetails():
        """Return a mutable dict mapping names to ``Content``."""

    def onException(exc_info, tb_label):
        """Called when we receive an exception.

        :param exc_info: A tuple of (exception_type, exception_value,
            traceback).
        :param tb_label: Used as the label for the traceback, if the traceback
            is to be attached as a detail.
        """


class IExtendedTestResult(Interface):
    """Receives test events."""

    def addExpectedFailure(test, err=None, details=None):
        """``test`` failed with an expected failure.

        For any given test, must be called after ``startTest`` was called for
        that test, and before ``stopTest`` has been called for that test.

        :param ITestCase test: The test that failed expectedly.
        :param exc_info err: An exc_info tuple.
        :param dict details: A map of names to ``Content`` objects.
        """

    def addError(test, err=None, details=None):
        """``test`` failed with an unexpected error.

        For any given test, must be called after ``startTest`` was called for
        that test, and before ``stopTest`` has been called for that test.

        :param ITestCase test: The test that raised an error.
        :param exc_info err: An exc_info tuple.
        :param dict details: A map of names to ``Content`` objects.
        """

    def addFailure(test, err=None, details=None):
        """``test`` failed as assertion.

        For any given test, must be called after ``startTest`` was called for
        that test, and before ``stopTest`` has been called for that test.

        :param ITestCase test: The test that raised an error.
        :param exc_info err: An exc_info tuple.
        :param dict details: A map of names to ``Content`` objects.
        """

    def addSkip(test, reason=None, details=None):
        """``test`` was skipped, rather than run.

        For any given test, must be called after ``startTest`` was called for
        that test, and before ``stopTest`` has been called for that test.

        :param ITestCase test: The test that raised an error.
        :param reason: The reason for the test being skipped.
        :param dict details: A map of names to ``Content`` objects.
        """

    def addSuccess(test, details=None):
        """``test`` run successfully.

        For any given test, must be called after ``startTest`` was called for
        that test, and before ``stopTest`` has been called for that test.

        :param ITestCase test: The test that raised an error.
        :param dict details: A map of names to ``Content`` objects.
        """

    def addUnexpectedSuccess(test, details=None):
        """``test`` was expected to fail, but succeeded.

        For any given test, must be called after ``startTest`` was called for
        that test, and before ``stopTest`` has been called for that test.

        :param ITestCase test: The test that raised an error.
        :param dict details: A map of names to ``Content`` objects.

        """

    def wasSuccessful():
        """Has this result been successful so far?"""

    def startTestRun():
        """Started a run of (potentially many) tests."""

    def stopTestRun():
        """Finished a run of (potentially many) tests."""

    def startTest(test):
        """``test`` started executing.

        Must be called after ``startTestRun`` and before ``stopTestRun``.

        :param ITestCase test: The test that started.
        """

    def stopTest(test):
        """``test`` stopped executing.

        Must be called after ``startTestRun`` and before ``stopTestRun``.

        :param ITestCase test: The test that stopped.
        """

    def tags(new_tags, gone_tags):
        """Change tags for the following tests.

        Updates ``current_tags`` such that all tags in ``new_tags`` are in
        ``current_tags`` and none of ``gone_tags`` are in ``current_tags``.

        :param set new_tags: A set of tags that will be applied to any
            following tests.
        :param set gone_tags: A set of tags that will no longer be applied to
            following tests.
        """

    def time(timestamp):
        """Tell the test result what the current time is.

        :param datetime timestamp: Either a time with timezone information, or
            ``None`` in which case the test result should get time from the
            system.
        """
