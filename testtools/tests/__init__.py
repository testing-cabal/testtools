"""Tests for testtools itself."""

# See README for copyright and licensing details.

import unittest


def test_suite():
    from testtools.tests import (
        test_compat,
        test_content,
        test_content_type,
        test_matchers,
        test_monkey,
        test_runtest,
        test_testtools,
        test_testresult,
        test_testsuite,
        )
    suites = []
    modules = [
        test_compat,
        test_content,
        test_content_type,
        test_matchers,
        test_monkey,
        test_runtest,
        test_testresult,
        test_testsuite,
        test_testtools,
        ]
    try:
        # Tests that rely on Twisted.
        from testtools.tests import (
            test_deferredruntest,
            test_spinner,
            )
    except ImportError:
        pass
    else:
        modules.extend([test_deferredruntest, test_spinner])
    try:
        # Tests that rely on 'fixtures'.
        from testtools.tests import (
            test_fixturesupport,
            )
    except ImportError:
        pass
    else:
        modules.extend([test_fixturesupport])

    for module in modules:
        suites.append(getattr(module, 'test_suite')())
    return unittest.TestSuite(suites)
