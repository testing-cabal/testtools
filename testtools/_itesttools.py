# Copyright (c) 2015 testtools developers. See LICENSE for details.

from zope.interface import Interface


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


class ITestCase(IRunnable):
    """An individual test case."""

    def __str__():
        """Return a short, human-readable description."""

    def id():
        """A unique identifier."""

    def shortDescription(self):
        """Return a short, human-readable description."""


class ITestCaseStrategy(Interface):
    """What ``RunTest`` needs to run a test case.

    This is a test that has a ``setUp``, a test body, and a ``tearDown``.
    """

    """Should local variables be captured in tracebacks?

    Can be mutated externally.
    """
    __testtools_tb_locals__ = False

    """List of ``(function, args, kwargs)`` called in reverse order after test.

    This list is mutated by ``RunTest``.
    """
    _cleanups = []

    """If non-False, then force the test to fail regardless of behavior.

    If not defined, assumed to be False.
    """
    force_failure = False

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
