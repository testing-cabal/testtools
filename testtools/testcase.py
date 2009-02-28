# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Test case related stuff."""

__metaclass__ = type
__all__ = [
    'change_test_id',
    'TestCase',
    ]

from copy import deepcopy
import unittest


class TestSkipped(Exception):
    """Raised within TestCase.run() when a test is skipped."""


class TestCase(unittest.TestCase):
    """Extensions to the basic TestCase."""

    skipException = TestSkipped

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self._cleanups = []
        self._last_unique_id = 0

    def shortDescription(self):
        return self.id()

    def skip(self, reason):
        """Cause this test to be skipped.

        This raises self.skipException(reason). skipException is raised
        to permit a skip to be triggered at any point(during setUp or the
        testMethod itself). The run() method catches skipException and
        translates that into a call to the result objects addSkip method.

        :param reason: The reason why the test is being skipped. This must
            support being cast into a unicode string for reporting.
        """
        raise self.skipException(reason)

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

        Cleanup functions are always called before a test finishes running,
        even if setUp is aborted by an exception.
        """
        self._cleanups.append((function, arguments, keywordArguments))

    def assertIn(self, needle, haystack):
        """Assert that needle is in haystack."""
        self.assertTrue(
            needle in haystack, '%r not in %r' % (needle, haystack))

    def assertIs(self, expected, observed):
        """Assert that `expected` is `observed`."""
        self.assertTrue(
            expected is observed, '%r is not %r' % (expected, observed))

    def assertIsNot(self, expected, observed):
        """Assert that `expected` is not `observed`."""
        self.assertTrue(
            expected is not observed, '%r is %r' % (expected, observed))

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

    def _handle_skip(self, result, reason):
        """Pass a skip to result.

        If result has an addSkip method, this is called. If not, addError is
        called instead.
        """
        addSkip = getattr(result, 'addSkip', None)
        if not callable(addSkip):
            result.addError(self, self._exc_info())
        else:
            addSkip(self, reason)

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
            except self.skipException, e:
                self._handle_skip(result, e.args[0])
                self._runCleanups(result)
                return
            except:
                result.addError(self, self._exc_info())
                self._runCleanups(result)
                return

            ok = False
            try:
                testMethod()
                ok = True
            except self.skipException, e:
                self._handle_skip(result, e.args[0])
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


def clone_test_with_new_id(test, new_id):
    """Copy a TestCase, and give the copied test a new id."""
    newTest = deepcopy(test)
    newTest.id = lambda: new_id
    return newTest

