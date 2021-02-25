# Copyright (c) 2010-2011 Testtools authors. See LICENSE for details.

"""Tests for the distutils test command logic."""

from distutils.dist import Distribution

import testtools
from testtools.compat import _b
from testtools.distutilscmd import TestCommand
from testtools.helpers import try_import
from testtools.matchers import MatchesRegex
from testtools import TestCase

fixtures = try_import('fixtures')


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
            super().setUp()
            self.useFixture(self.package)
            testtools.__path__.append(self.package.base)
            self.addCleanup(testtools.__path__.remove, self.package.base)


class TestCommandTest(TestCase):

    def setUp(self):
        super().setUp()
        if fixtures is None:
            self.skipTest("Need fixtures")

    def test_test_module(self):
        self.useFixture(SampleTestFixture())
        stdout = self.useFixture(fixtures.StringStream('stdout'))
        dist = Distribution()
        dist.script_name = 'setup.py'
        dist.script_args = ['test']
        dist.cmdclass = {'test': TestCommand}
        dist.command_options = {
            'test': {'test_module': ('command line', 'testtools.runexample')}}
        with fixtures.MonkeyPatch('sys.stdout', stdout.stream):
            cmd = dist.reinitialize_command('test')
            dist.run_command('test')
        self.assertThat(
            stdout.getDetails()['stdout'].as_text(),
            MatchesRegex("""Tests running...

Ran 2 tests in \\d.\\d\\d\\ds
OK
"""))

    def test_test_suite(self):
        self.useFixture(SampleTestFixture())
        stdout = self.useFixture(fixtures.StringStream('stdout'))
        dist = Distribution()
        dist.script_name = 'setup.py'
        dist.script_args = ['test']
        dist.cmdclass = {'test': TestCommand}
        dist.command_options = {
            'test': {
                'test_suite': (
                    'command line', 'testtools.runexample.test_suite')}}
        with fixtures.MonkeyPatch('sys.stdout', stdout.stream):
            cmd = dist.reinitialize_command('test')
            dist.run_command('test')
        self.assertThat(
            stdout.getDetails()['stdout'].as_text(),
            MatchesRegex("""Tests running...

Ran 2 tests in \\d.\\d\\d\\ds
OK
"""))


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
