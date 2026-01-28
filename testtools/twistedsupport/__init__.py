# Copyright (c) 2016 testtools developers. See LICENSE for details.

"""Support for testing code that uses Twisted."""

__all__ = [
    # Running tests
    "AsynchronousDeferredRunTest",
    "AsynchronousDeferredRunTestForBrokenTwisted",
    "CaptureTwistedLogs",
    # Deferred utilities
    "DeferredNotFired",
    "SynchronousDeferredRunTest",
    "assert_fails_with",
    "extract_result",
    "failed",
    "flush_logged_errors",
    "has_no_result",
    # Matchers
    "succeeded",
]

from ._deferred import (
    DeferredNotFired,
    extract_result,
)
from ._matchers import (
    failed,
    has_no_result,
    succeeded,
)
from ._runtest import (
    AsynchronousDeferredRunTest,
    AsynchronousDeferredRunTestForBrokenTwisted,
    CaptureTwistedLogs,
    SynchronousDeferredRunTest,
    assert_fails_with,
    flush_logged_errors,
)
