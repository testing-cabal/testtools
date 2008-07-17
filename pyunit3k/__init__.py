# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Extensions to the standard Python unittest library."""

__all__ = [
    'iterate_tests',
    'ITestResult',
    'MultiTestResult',
    'TestCase',
    'TestResult',
    ]

from copy import deepcopy
import unittest

from zope.interface import implements

from pyunit3k.interfaces import ITestResult


class TestResult(unittest.TestResult):

    implements(ITestResult)

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

    def addSuccess(self, test):
        self._dispatch('addSuccess', test)

    def done(self):
        self._dispatch('done')


class TestCase(unittest.TestCase):
    """Extensions to the basic TestCase."""

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self._cleanups = []
        self._last_unique_id = 0

    def shortDescription(self):
        return self.id()

    def _formatTypes(self, classOrIterable):
        """Format a class or a bunch of classes for display in an error."""
        className = getattr(classOrIterable, '__name__', None)
        if className is None:
            className = ', '.join(klass.__name__ for klass in classOrIterable)
        return className

    def _runCleanups(self, result):
        """Run the cleanups that have been added with addCleanup.

        See the docstring for addCleanup for more information.

        Returns True if all cleanups ran without error, False otherwise.
        """
        ok = True
        while self._cleanups:
            function, arguments, keywordArguments = self._cleanups.pop()
            try:
                function(*arguments, **keywordArguments)
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._exc_info())
                ok = False
        return ok

    def addCleanup(self, function, *arguments, **keywordArguments):
        """Add a cleanup function to be called before tearDown.

        Functions added with addCleanup will be called in reverse order of
        adding after the test method and before tearDown.

        If a function added with addCleanup raises an exception, the error
        will be recorded as a test error, and the next cleanup will then be
        run.
        """
        self._cleanups.append((function, arguments, keywordArguments))

    def assertIn(self, needle, haystack):
        """Assert that needle is in haystack."""
        self.assertTrue(
            needle in haystack, '%r not in %r' % (needle, haystack))

    def assertNotIn(self, needle, haystack):
        """Assert that needle is not in haystack."""
        self.assertTrue(
            needle not in haystack, '%r in %r' % (needle, haystack))

    def assertIsInstance(self, obj, klass):
        self.assertTrue(
            isinstance(obj, klass),
            '%r is not an instance of %s' % (obj, self._formatTypes(klass)))

    def assertRaises(self, excClass, callableObj, *args, **kwargs):
        """Fail unless an exception of class excClass is thrown
           by callableObj when invoked with arguments args and keyword
           arguments kwargs. If a different type of exception is
           thrown, it will not be caught, and the test case will be
           deemed to have suffered an error, exactly as for an
           unexpected exception.
        """
        try:
            ret = callableObj(*args, **kwargs)
        except excClass, excObject:
            return excObject
        else:
            excName = self._formatTypes(excClass)
            self.fail("%s not raised, %r returned instead." % (excName, ret))
    failUnlessRaises = assertRaises

    def getUniqueInteger(self):
        self._last_unique_id += 1
        return self._last_unique_id

    def getUniqueString(self):
        return '%s-%d' % (self._testMethodName, self.getUniqueInteger())

    def runTest(self):
        """Define this so we can construct a null test object."""

    def run(self, result=None):
        if result is None:
            result = self.defaultTestResult()
        result.startTest(self)
        testMethod = getattr(self, self._testMethodName)
        try:
            try:
                self.setUp()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._exc_info())
                self._runCleanups(result)
                return

            ok = False
            try:
                testMethod()
                ok = True
            except self.failureException:
                result.addFailure(self, self._exc_info())
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._exc_info())

            cleanupsOk = self._runCleanups(result)
            try:
                self.tearDown()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._exc_info())
                ok = False
            if ok and cleanupsOk:
                result.addSuccess(self)
        finally:
            result.stopTest(self)


def change_test_id(test, new_id):
    new_test = deepcopy(test)
    new_test.id = lambda: new_id
    return new_test


def iterate_tests(test_suite_or_case):
    """Iterate through all of the test cases in `test_suite_or_case`."""
    try:
        suite = iter(test_suite_or_case)
    except TypeError:
        yield test_suite_or_case
    else:
        for test in suite:
            for subtest in iterate_tests(test):
                yield subtest
