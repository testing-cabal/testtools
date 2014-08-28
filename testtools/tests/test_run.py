# Copyright (c) 2010 testtools developers. See LICENSE for details.

"""Tests for the test runner logic."""

from unittest import TestSuite
import sys
from textwrap import dedent

from extras import try_import
fixtures = try_import('fixtures')
testresources = try_import('testresources')

import testtools
from testtools import TestCase, run, skipUnless
from testtools.compat import (
    _b,
    _u,
    StringIO,
    )
from testtools.matchers import (
    Contains,
    MatchesRegex,
    )


if fixtures:
    class SampleTestFixture(fixtures.Fixture):
        """Creates testtools.runexample temporarily."""

        def __init__(self, broken=False):
            """Create a SampleTestFixture.

            :param broken: If True, the sample file will not be importable.
            """
            if not broken:
                init_contents = _b("""\
from testtools import TestCase

class TestFoo(TestCase):
    def test_bar(self):
        pass
    def test_quux(self):
        pass
def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
""")
            else:
                init_contents = b"class not in\n"
            self.package = fixtures.PythonPackage(
            'runexample', [('__init__.py', init_contents)])

        def setUp(self):
            super(SampleTestFixture, self).setUp()
            self.useFixture(self.package)
            testtools.__path__.append(self.package.base)
            self.addCleanup(testtools.__path__.remove, self.package.base)
            self.addCleanup(sys.modules.pop, 'testtools.runexample', None)


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


if fixtures and run.have_discover:
    class SampleLoadTestsPackage(fixtures.Fixture):
        """Creates a test suite package using load_tests."""

        def __init__(self):
            super(SampleLoadTestsPackage, self).__init__()
            self.package = fixtures.PythonPackage(
            'discoverexample', [('__init__.py', _b("""
from testtools import TestCase, clone_test_with_new_id

class TestExample(TestCase):
    def test_foo(self):
        pass

def load_tests(loader, tests, pattern):
    tests.addTest(clone_test_with_new_id(tests._tests[1]._tests[0], "fred"))
    return tests
"""))])

        def setUp(self):
            super(SampleLoadTestsPackage, self).setUp()
            self.useFixture(self.package)
            self.addCleanup(sys.path.remove, self.package.base)


class TestRun(TestCase):

    def setUp(self):
        super(TestRun, self).setUp()
        if fixtures is None:
            self.skipTest("Need fixtures")

    def test_run_custom_list(self):
        self.useFixture(SampleTestFixture())
        tests = []
        class CaptureList(run.TestToolsTestRunner):
            def list(self, test):
                tests.append(set([case.id() for case
                    in testtools.testsuite.iterate_tests(test)]))
        out = StringIO()
        try:
            program = run.TestProgram(
                argv=['prog', '-l', 'testtools.runexample.test_suite'],
                stdout=out, testRunner=CaptureList)
        except SystemExit:
            exc_info = sys.exc_info()
            raise AssertionError("-l tried to exit. %r" % exc_info[1])
        self.assertEqual([set(['testtools.runexample.TestFoo.test_bar',
            'testtools.runexample.TestFoo.test_quux'])], tests)

    def test_run_list(self):
        self.useFixture(SampleTestFixture())
        out = StringIO()
        try:
            run.main(['prog', '-l', 'testtools.runexample.test_suite'], out)
        except SystemExit:
            exc_info = sys.exc_info()
            raise AssertionError("-l tried to exit. %r" % exc_info[1])
        self.assertEqual("""testtools.runexample.TestFoo.test_bar
testtools.runexample.TestFoo.test_quux
""", out.getvalue())

    def test_run_list_failed_import(self):
        if not run.have_discover:
            self.skipTest("Need discover")
        broken = self.useFixture(SampleTestFixture(broken=True))
        out = StringIO()
        exc = self.assertRaises(
            SystemExit,
            run.main, ['prog', 'discover', '-l', broken.package.base, '*.py'], out)
        self.assertEqual(2, exc.args[0])
        self.assertEqual("""Failed to import
runexample
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
        try:
            run.main(['prog', '-l', '--load-list', tempname,
                'testtools.runexample.test_suite'], out)
        except SystemExit:
            exc_info = sys.exc_info()
            raise AssertionError("-l tried to exit. %r" % exc_info[1])
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
        try:
            run.main(['prog', '-l', '--load-list', tempname,
                'testtools.runexample.test_suite'], out)
        except SystemExit:
            exc_info = sys.exc_info()
            raise AssertionError("-l tried to exit. %r" % exc_info[1])
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
        with fixtures.MonkeyPatch('sys.stdout', stdout.stream):
            runner = run.TestToolsTestRunner(failfast=True)
            runner.run(TestSuite([Failing('test_a'), Failing('test_b')]))
        self.assertThat(
            stdout.getDetails()['stdout'].as_text(), Contains('Ran 1 test'))

    def test_stdout_honoured(self):
        self.useFixture(SampleTestFixture())
        tests = []
        out = StringIO()
        exc = self.assertRaises(SystemExit, run.main,
            argv=['prog', 'testtools.runexample.test_suite'],
            stdout=out)
        self.assertEqual((0,), exc.args)
        self.assertThat(
            out.getvalue(),
            MatchesRegex(_u("""Tests running...

Ran 2 tests in \\d.\\d\\d\\ds
OK
""")))

    @skipUnless(run.have_discover, "discovery not present")
    @skipUnless(fixtures, "fixtures not present")
    def test_issue_16662(self):
        # unittest's discover implementation didn't handle load_tests on
        # packages. That is fixed pending commit, but we want to offer it
        # to all testtools users regardless of Python version.
        # See http://bugs.python.org/issue16662
        pkg = self.useFixture(SampleLoadTestsPackage())
        out = StringIO()
        self.assertEqual(None, run.main(
            ['prog', 'discover', '-l', pkg.package.base], out))
        self.assertEqual(dedent("""\
            discoverexample.TestExample.test_foo
            fred
            """), out.getvalue())


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
