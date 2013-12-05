import unittest

import manuel.codeblock
import manuel.testing


def test_suite():
    m = manuel.codeblock.Manuel()
    return manuel.testing.TestSuite(m, 'for-test-authors.rst')

if __name__ == '__main__':
    result = unittest.TextTestRunner().run(test_suite())
    assert result.wasSuccessful()
