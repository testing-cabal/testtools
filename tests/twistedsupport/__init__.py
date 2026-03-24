# Copyright (c) testtools developers. See LICENSE for details.

import warnings
from unittest import TestSuite

# Twisted holds a /dev/null fd open at the module level as an EMFILE recovery
# reserve (twisted.internet.tcp._reservedFD). It is intentionally never closed,
# so it triggers a ResourceWarning at interpreter shutdown. Filter it here,
# scoped to the Twisted test package, so genuine leaks elsewhere are still
# reported.
warnings.filterwarnings(
    "ignore",
    message=r"unclosed file.*name='/dev/null'",
    category=ResourceWarning,
)


def test_suite():
    from . import (
        test_deferred,
        test_matchers,
        test_runtest,
        test_spinner,
    )

    modules = [
        test_deferred,
        test_matchers,
        test_runtest,
        test_spinner,
    ]
    suites = map(lambda x: x.test_suite(), modules)
    return TestSuite(suites)
