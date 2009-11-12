# Copyright (c) 2009 Jonathan M. Lange. See LICENSE for details.

"""Tests for the RunTest single test execution logic."""

import unittest

from testtools import (
    ExtendedToOriginalDecorator,
    RunTest,
    TestCase,
    TestResult,
    )
from testtools.tests.helpers import (
    LoggingResult,
    Python26TestResult,
    Python27TestResult,
    ExtendedTestResult,
    )


class TestRunTest(TestCase):
    
    def make_case(self):
        class Case(TestCase):
            def test(self):
                pass
        return Case('test')

    def test___init__(self):
        run = RunTest("bar", "foo")
        self.assertEqual(run.case, "bar")
        # to transition code we pass the existing run logic into RunTest.
        self.assertEqual(run.wrapped, "foo")

    def test___call__(self):
        # run() invokes wrapped
        log = []
        run = RunTest(self, lambda x:log.append('foo'))
        run()
        self.assertEqual(['foo'], log)

    def test___call___with_result(self):
        # run() invokes wrapped
        log = []
        run = RunTest("bar", lambda x:log.append(x))
        run('foo')
        self.assertEqual(1, len(log))
        self.assertEqual('foo', log[0].decorated)

    def test___call___no_result_manages_new_result(self):
        log = []
        run = RunTest(self.make_case(), lambda x:log.append(x) or x)
        result = run()
        self.assertEqual([result], log)
        self.assertIsInstance(log[0].decorated, TestResult)

    def test__run_one_decorates_result(self):
        log = []
        class Run(RunTest):
            def _run_decorated_result(self, result):
                log.append(result)
                return result
        run = Run(self.make_case(), lambda x:x)
        result = run._run_one('foo')
        self.assertEqual([result], log)
        self.assertIsInstance(log[0], ExtendedToOriginalDecorator)
        self.assertEqual('foo', result.decorated)


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
