# Copyright (c) testtools developers. See LICENSE for details.

"""Support for testing code that uses Twisted."""

__all__ = [
    # Matchers
    'succeeded',
    'failed',
    'NO_RESULT',

    # Running tests
    'AsynchronousDeferredRunTest',
    'AsynchronousDeferredRunTestForBrokenTwisted',
    'SynchronousDeferredRunTest',
    'assert_fails_with',
    'flush_logged_errors',
]

from ._deferredmatchers import (
    succeeded,
    failed,
    NO_RESULT,
)

from .deferredruntest import (
    AsynchronousDeferredRunTest,
    AsynchronousDeferredRunTestForBrokenTwisted,
    SynchronousDeferredRunTest,
    assert_fails_with,
    flush_logged_errors,
)
