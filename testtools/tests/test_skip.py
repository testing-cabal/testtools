"""
Note that the testtools.skipIf decorated testtools.TestCase doesn't show up in
the results when run with trial.

$ trial testtools.tests.test_skip
testtools.tests.test_skip
  TestCaseWithUnittest
    test_skip ...                                                     [SKIPPED]

===============================================================================
[SKIPPED]
TestCase skipped

testtools.tests.test_skip.TestCaseWithUnittest.test_skip
-------------------------------------------------------------------------------
Ran 1 tests in 0.015s

PASSED (skips=1)

And when I attempt to run the testtools TestCase directly I get the following error:

$ trial testtools.tests.test_skip.TestCaseWithTesttools
Traceback (most recent call last):
  File "/home/richard/.virtualenvs/testtools-205/bin/trial", line 22, in <module>
    run()
  File "/home/richard/.virtualenvs/testtools-205/lib/python2.7/site-packages/twisted/scripts/trial.py", line 612, in run
    suite = _getSuite(config)
  File "/home/richard/.virtualenvs/testtools-205/lib/python2.7/site-packages/twisted/scripts/trial.py", line 500, in _getSuite
    return loader.loadByNames(config['tests'], recurse=recurse)
  File "/home/richard/.virtualenvs/testtools-205/lib/python2.7/site-packages/twisted/trial/runner.py", line 609, in loadByNames
    for thing in self._uniqueTests(things)]
  File "/home/richard/.virtualenvs/testtools-205/lib/python2.7/site-packages/twisted/trial/runner.py", line 573, in loadAnything
    raise TypeError("No loader for %r. Unrecognized type" % (thing,))
TypeError: No loader for <function TestCaseWithTesttools at 0x7f71d6406aa0>. Unrecognized type

"""

from unittest import (
    TestCase as UnittestTestCase,
    skipIf as unittest_skipIf,
)
from testtools import (
    TestCase as TesttoolsTestCase,
    skipIf as testtools_skipIf,
)


@testtools_skipIf(True, "TestCase skipped")
class TestCaseWithTesttools(TesttoolsTestCase):
    """
    This TestCase doesn't show.
    """
    def test_skip(self):
        self.fail("This shouldn't run")


@unittest_skipIf(True, "TestCase skipped")
class TestCaseWithUnittest(UnittestTestCase):
    """
    This TestCase shows as skipped.
    """
    def test_skip(self):
        self.fail("This shouldn't run")
