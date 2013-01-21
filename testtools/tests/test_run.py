# Copyright (c) 2010 testtools developers. See LICENSE for details.

"""Tests for the test runner logic."""

from unittest import TestSuite

from extras import try_import
fixtures = try_import('fixtures')
testresources = try_import('testresources')

import testtools
from testtools import TestCase, run
from testtools.compat import (
    _b,
    StringIO,
    )
from testtools.matchers import Contains


if fixtures:
    class SampleTestFixture(fixtures.Fixture):
        """Creates testtools.runexample temporarily."""

        def __init__(self):
            self.package = fixtures.PythonPackage(
            'runexample', [('__init__.py', _b("""
from testtools import TestCase

class TestFoo(TestCase):
    def test_bar(self):
        pass
    def test_quux(self):
        pass
def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
"""))])

        def setUp(self):
            super(SampleTestFixture, self).setUp()
            self.useFixture(self.package)
            testtools.__path__.append(self.package.base)
            self.addCleanup(testtools.__path__.remove, self.package.base)


if fixtures and testresources:
    class SampleResourcedFixture(fixtures.Fixture):
        """Creates a test suite that uses testresources."""

        def __init__(self):
            super(SampleResourcedFixture, self).__init__()
            self.package = fixtures.PythonPackage(
            'resourceexample', [('__init__.py', _b("""
from fixtures import Fixture
from testresources import (
    FixtureResource,
    OptimisingTestSuite,
    ResourcedTestCase,
    )
from testtools import TestCase

class Printer(Fixture):

    def setUp(self):
        super(Printer, self).setUp()
        print('Setting up Printer')

    def reset(self):
        pass

class TestFoo(TestCase, ResourcedTestCase):
    # When run, this will print just one Setting up Printer, unless the
    # OptimisingTestSuite is not honoured, when one per test case will print.
    resources=[('res', FixtureResource(Printer()))]
    def test_bar(self):
        pass
    def test_foo(self):
        pass
    def test_quux(self):
        pass
def test_suite():
    from unittest import TestLoader
    return OptimisingTestSuite(TestLoader().loadTestsFromName(__name__))
"""))])

        def setUp(self):
            super(SampleResourcedFixture, self).setUp()
            self.useFixture(self.package)
            self.addCleanup(testtools.__path__.remove, self.package.base)
            testtools.__path__.append(self.package.base)


class TestRun(TestCase):

    def setUp(self):
        super(TestRun, self).setUp()
        if fixtures is None:
            self.skipTest("Need fixtures")

    def test_run_list(self):
        self.useFixture(SampleTestFixture())
        out = StringIO()
        run.main(['prog', '-l', 'testtools.runexample.test_suite'], out)
        self.assertEqual("""testtools.runexample.TestFoo.test_bar
testtools.runexample.TestFoo.test_quux
""", out.getvalue())

    def test_run_orders_tests(self):
        self.useFixture(SampleTestFixture())
        out = StringIO()
        # We load two tests - one that exists and one that doesn't, and we
        # should get the one that exists and neither the one that doesn't nor
        # the unmentioned one that does.
        tempdir = self.useFixture(fixtures.TempDir())
        tempname = tempdir.path + '/tests.list'
        f = open(tempname, 'wb')
        try:
            f.write(_b("""
testtools.runexample.TestFoo.test_bar
testtools.runexample.missingtest
"""))
        finally:
            f.close()
        run.main(['prog', '-l', '--load-list', tempname,
            'testtools.runexample.test_suite'], out)
        self.assertEqual("""testtools.runexample.TestFoo.test_bar
""", out.getvalue())

    def test_run_load_list(self):
        self.useFixture(SampleTestFixture())
        out = StringIO()
        # We load two tests - one that exists and one that doesn't, and we
        # should get the one that exists and neither the one that doesn't nor
        # the unmentioned one that does.
        tempdir = self.useFixture(fixtures.TempDir())
        tempname = tempdir.path + '/tests.list'
        f = open(tempname, 'wb')
        try:
            f.write(_b("""
testtools.runexample.TestFoo.test_bar
testtools.runexample.missingtest
"""))
        finally:
            f.close()
        run.main(['prog', '-l', '--load-list', tempname,
            'testtools.runexample.test_suite'], out)
        self.assertEqual("""testtools.runexample.TestFoo.test_bar
""", out.getvalue())

    def test_load_list_preserves_custom_suites(self):
        if testresources is None:
            self.skipTest("Need testresources")
        self.useFixture(SampleResourcedFixture())
        # We load two tests, not loading one. Both share a resource, so we
        # should see just one resource setup occur.
        tempdir = self.useFixture(fixtures.TempDir())
        tempname = tempdir.path + '/tests.list'
        f = open(tempname, 'wb')
        try:
            f.write(_b("""
testtools.resourceexample.TestFoo.test_bar
testtools.resourceexample.TestFoo.test_foo
"""))
        finally:
            f.close()
        stdout = self.useFixture(fixtures.StringStream('stdout'))
        with fixtures.MonkeyPatch('sys.stdout', stdout.stream):
            try:
                run.main(['prog', '--load-list', tempname,
                    'testtools.resourceexample.test_suite'], stdout.stream)
            except SystemExit:
                # Evil resides in TestProgram.
                pass
        out = stdout.getDetails()['stdout'].as_text()
        self.assertEqual(1, out.count('Setting up Printer'), "%r" % out)

    def test_run_failfast(self):
        stdout = self.useFixture(fixtures.StringStream('stdout'))

        class Failing(TestCase):
            def test_a(self):
                self.fail('a')
            def test_b(self):
                self.fail('b')
        runner = run.TestToolsTestRunner(failfast=True)
        with fixtures.MonkeyPatch('sys.stdout', stdout.stream):
            runner.run(TestSuite([Failing('test_a'), Failing('test_b')]))
        self.assertThat(
            stdout.getDetails()['stdout'].as_text(), Contains('Ran 1 test'))



def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
