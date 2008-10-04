# See README for copyright and licensing details.

import unittest
from testtools.tests import test_testtools, test_testresult


def test_suite():
    return unittest.TestSuite(
        [test_testtools.test_suite(), test_testresult.test_suite()])
