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
        result = TestResult()
        run(result)
        self.assertEqual(1, len(log))
        self.assertEqual(result, log[0].decorated)

    def test___call___no_result_manages_new_result(self):
        log = []
        run = RunTest(self.make_case(), lambda x:log.append(x) or x)
        result = run()
        self.assertEqual([result], log)
        self.assertIsInstance(log[0].decorated, TestResult)

    def test__run_one_decorates_result(self):
        log = []
        class Run(RunTest):
            def _run_prepared_result(self, result):
                log.append(result)
                return result
        run = Run(self.make_case(), lambda x:x)
        result = run._run_one('foo')
        self.assertEqual([result], log)
        self.assertIsInstance(log[0], ExtendedToOriginalDecorator)
        self.assertEqual('foo', result.decorated)

    def test__run_prepared_result_calls_start_and_stop_test(self):
        result = ExtendedTestResult()
        case = self.make_case()
        run = RunTest(case, lambda x:x)
        run(result)
        self.assertEqual([
            ('startTest', case),
            ('stopTest', case),
            ], result._events)

    def test__run_prepared_result_calls_stop_test_always(self):
        result = ExtendedTestResult()
        case = self.make_case()
        def inner(result):
            raise Exception("foo")
            return result
        run = RunTest(case, inner)
        self.assertRaises(Exception, run, result)
        self.assertEqual([
            ('startTest', case),
            ('stopTest', case),
            ], result._events)

def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
