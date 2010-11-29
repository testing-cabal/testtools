# Copyright (c) 2010 Testtools authors. See LICENSE for details.

"""Tests for the test runner logic."""

import StringIO

from testtools.helpers import try_import
fixtures = try_import('fixtures')

import testtools
from testtools import TestCase, run


class TestRun(TestCase):

    def test_run_list(self):
        if fixtures is None:
            self.skipTest("Need fixtures")
        package = self.useFixture(fixtures.PythonPackage(
            'runexample', [('__init__.py', """
from testtools import TestCase

class TestFoo(TestCase):
    def test_bar(self):
        pass
    def test_quux(self):
        pass
def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
""")]))
        testtools.__path__.append(package.base)
        self.addCleanup(testtools.__path__.remove, package.base)
        out = StringIO.StringIO()
        run.main(['-l', 'testtools.runexample.test_suite'], out)
        self.assertEqual("""testtools.runexample.TestFoo.test_bar
testtools.runexample.TestFoo.test_quux
""", out.getvalue())

def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
