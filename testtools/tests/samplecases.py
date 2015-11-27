# Copyright (c) 2015 testtools developers. See LICENSE for details.

"""A collection of sample TestCases.

These are primarily of use in testing the test framework.
"""

from testtools import TestCase


class _NormalTest(TestCase):

    def test_success(self):
        pass

    def test_error(self):
        1/0

    def test_failure(self):
        self.fail('arbitrary failure')


"""
A list that can be used with testscenarios to test every kind of sample
case that we have.
"""
all_sample_cases_scenarios = [
    ('simple-success-test', {'case': _NormalTest('test_success')}),
    ('simple-error-test', {'case': _NormalTest('test_error')}),
    ('simple-failure-test', {'case': _NormalTest('test_failure')}),
]
