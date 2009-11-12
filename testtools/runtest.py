# Copyright (c) 2009 Jonathan M. Lange. See LICENSE for details.

"""Individual test case execution."""

__metaclass__ = type
__all__ = [
    'RunTest',
    ]


class RunTest:
    """An object to run a test.

    RunTest objects are used to implement the internal logic involved in
    running a test. TestCase.__init__ stores _RunTest as the class of RunTest
    to execute.  Passing the runTest= parameter to TestCase.__init__ allows a
    different RunTest class to be used to execute the test.

    Subclassing or replacing RunTest can be useful to add functionality to the
    way that tests are run in a given project.

    :ivar wrapped: The original run method that is invoked once RunTest 
        specific code has completed.  This ivar is a transitional measure that
        will be removed once all the code has migrated.
    :ivar case: The test case that is to be run.
    """

    def __init__(self, case, original_run):
        """Create a RunTest to run case that will hand off to original_run.
        
        :param case: A testtools.TestCase test case object.
        """
        self.wrapped = original_run
        self.case = case

    def __call__(self, result=None):
        """Run self.case reporting activity to result.

        :param result: Optional testtools.TestResult to report activity to.
        :return: The result object the test was run against.
        """
        if result is None:
            actual_result = self.case.defaultTestResult()
            actual_result.startTestRun()
        else:
            actual_result = result
        try:
            return self.run_one(actual_result)
        finally:
            if result is None:
                actual_result.stopTestRun()

    def run_one(self, result):
        """Run one test reporting to result.

        :param result: testtools.TestResult to report activity to.
        :return: The result object the test was run against.
        """
        return self.wrapped(result)
