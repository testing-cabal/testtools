# Copyright (c) 2015 testtools developers. See LICENSE for details.

"""A collection of sample TestCases.

These are primarily of use in testing the test framework.
"""

from testtools import TestCase
from testtools.matchers import (
    AfterPreprocessing,
    Contains,
    Equals,
    MatchesDict,
    MatchesListwise,
)


class _NormalTest(TestCase):

    def test_success(self):
        pass

    def test_error(self):
        1/0

    def test_failure(self):
        self.fail('arbitrary failure')


class _TearDownFails(TestCase):
    """Passing test case with failing tearDown after upcall."""

    def test_success(self):
        pass

    def tearDown(self):
        super(_TearDownFails, self).tearDown()
        1/0


class _SetUpFailsOnGlobalState(TestCase):
    """Fail to upcall setUp on first run. Fail to upcall tearDown after.

    This simulates a test that fails to upcall in ``setUp`` if some global
    state is broken, and fails to call ``tearDown`` at all.
    """

    first_run = True

    def setUp(self):
        if not self.first_run:
            return
        super(_SetUpFailsOnGlobalState, self).setUp()

    def test_success(self):
        pass

    def tearDown(self):
        if not self.first_run:
            super(_SetUpFailsOnGlobalState, self).tearDown()
        self.__class__.first_run = False

    @classmethod
    def make_scenario(cls):
        case = cls('test_success')
        return {
            'case': case,
            'expected_first_result': _test_error_traceback(
                case, Contains('TestCase.tearDown was not called')),
            'expected_second_result': _test_error_traceback(
                case, Contains('TestCase.setUp was not called')),
        }


def _test_error_traceback(case, traceback_matcher):
    """Match result log of single test that errored out.

    ``traceback_matcher`` is applied to the text of the traceback.
    """
    return MatchesListwise([
        Equals(('startTest', case)),
        MatchesListwise([
            Equals('addError'),
            Equals(case),
            MatchesDict({
                'traceback': AfterPreprocessing(
                    lambda x: x.as_text(),
                    traceback_matcher,
                )
            })
        ]),
        Equals(('stopTest', case)),
    ])


"""
A list that can be used with testscenarios to test every deterministic sample
case that we have.
"""
deterministic_sample_cases_scenarios = [
    ('simple-success-test', {'case': _NormalTest('test_success')}),
    ('simple-error-test', {'case': _NormalTest('test_error')}),
    ('simple-failure-test', {'case': _NormalTest('test_failure')}),
    ('teardown-fails', {'case': _TearDownFails('test_success')}),
]


"""
A list that can be used with testscenarios to test every non-deterministic
sample case that we have.
"""
nondeterministic_sample_cases_scenarios = [
    ('setup-fails-global-state', _SetUpFailsOnGlobalState.make_scenario()),
]
