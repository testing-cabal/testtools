# Copyright (c) 2010 Testtools authors. See LICENSE for details.

"""Tests for the test runner logic."""

import StringIO

from testtools.helpers import try_import
fixtures = try_import('fixtures')

import testtools
from testtools import TestCase, run


if fixtures:
    class SampleTestFixture(fixtures.Fixture):
        """Creates testtools.runexample temporarily."""

        def __init__(self):
            self.package = fixtures.PythonPackage(
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
""")])

        def setUp(self):
            super(SampleTestFixture, self).setUp()
            self.useFixture(self.package)
            testtools.__path__.append(self.package.base)
            self.addCleanup(testtools.__path__.remove, self.package.base)


class TestRun(TestCase):

    def test_run_list(self):
        if fixtures is None:
            self.skipTest("Need fixtures")
        package = self.useFixture(SampleTestFixture())
        out = StringIO.StringIO()
        run.main(['-l', 'testtools.runexample.test_suite'], out)
        self.assertEqual("""testtools.runexample.TestFoo.test_bar
testtools.runexample.TestFoo.test_quux
""", out.getvalue())

def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
