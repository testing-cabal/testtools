# Copyright (c) 2008-2015 testtools developers. See LICENSE for details.

"""Tests for testtools itself."""

from unittest import TestSuite

import testscenarios


def test_suite():
    from testtools.tests import (
        matchers,
        test_assert_that,
        test_compat,
        test_content,
        test_content_type,
        test_deferred,
        test_deferredmatchers,
        test_deferredruntest,
        test_distutilscmd,
        test_fixturesupport,
        test_helpers,
        test_monkey,
        test_run,
        test_runtest,
        test_spinner,
        test_tags,
        test_testcase,
        test_testresult,
        test_testsuite,
        test_with_with,
        )
    modules = [
        matchers,
        test_assert_that,
        test_compat,
        test_content,
        test_content_type,
        test_deferred,
        test_deferredmatchers,
        test_deferredruntest,
        test_distutilscmd,
        test_fixturesupport,
        test_helpers,
        test_monkey,
        test_run,
        test_runtest,
        test_spinner,
        test_tags,
        test_testcase,
        test_testresult,
        test_testsuite,
        test_with_with,
        ]
    suites = map(lambda x: x.test_suite(), modules)
    all_tests = TestSuite(suites)
    return TestSuite(testscenarios.generate_scenarios(all_tests))
