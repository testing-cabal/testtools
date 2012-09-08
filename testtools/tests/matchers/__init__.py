# Copyright (c) 2009-2012 testtools developers. See LICENSE for details.


from unittest import TestSuite


def test_suite():
    from testtools.tests.matchers import (
        test_basic,
        test_core,
        test_datastructures,
        test_dict,
        test_doctest,
        test_exception,
        test_filesystem,
        test_higherorder,
        )
    modules = [
        test_basic,
        test_core,
        test_datastructures,
        test_dict,
        test_doctest,
        test_exception,
        test_filesystem,
        test_higherorder,
        ]
    suites = map(lambda x: x.test_suite(), modules)
    return TestSuite(suites)
