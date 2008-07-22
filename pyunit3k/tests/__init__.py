# See README for copyright and licensing details.

import unittest
from pyunit3k.tests import test_pyunit3k, test_testresult


def test_suite():
    return unittest.TestSuite(
        [test_pyunit3k.test_suite(), test_testresult.test_suite()])
