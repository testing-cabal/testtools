# Copyright (c) testtools developers. See LICENSE for details.

"""Tests for Deferred matchers."""

from extras import try_import

from testtools.compat import _u
from testtools._deferredmatchers import (
    no_result,
)
from testtools.matchers import (
    AfterPreprocessing,
    Equals,
    Is,
    MatchesDict,
)
from testtools.tests.test_spinner import NeedsTwistedTestCase


defer = try_import('twisted.internet.defer')
failure = try_import('twisted.python.failure')


def mismatches(description, details=None):
    """Match a ``Mismatch`` object."""
    if details is None:
        details = Equals({})

    matcher = MatchesDict({
        'description': description,
        'details': details,
    })

    def get_mismatch_info(mismatch):
        return {
            'description': mismatch.describe(),
            'details': mismatch.get_details(),
        }

    return AfterPreprocessing(get_mismatch_info, matcher)


def make_failure(exc_value):
    """Raise ``exc_value`` and return the failure."""
    try:
        raise exc_value
    except:
        return failure.Failure()


class NoResultTests(NeedsTwistedTestCase):
    """
    Tests for ``no_result``.
    """

    def match(self, thing):
        return no_result().match(thing)

    def test_unfired_matches(self):
        # A Deferred that hasn't fired matches no_result.
        self.assertThat(self.match(defer.Deferred()), Is(None))

    def test_successful_does_no_match(self):
        # A Deferred that's fired successfully does not match no_result.
        result = None
        deferred = defer.succeed(result)
        mismatch = self.match(deferred)
        self.assertThat(
            mismatch, mismatches(Equals(_u(
                '%r has already fired with %r' % (deferred, result)))))

    def test_failed_does_not_match(self):
        # A Deferred that's failed does not match no_result.
        fail = make_failure(RuntimeError('arbitrary failure'))
        deferred = defer.fail(fail)
        # Suppress unhandled error in Deferred.
        self.addCleanup(deferred.addErrback, lambda _: None)
        mismatch = self.match(deferred)
        self.assertThat(
            mismatch, mismatches(Equals(_u(
                '%r has already fired with %r' % (deferred, fail)))))

    def test_success_after_assertion(self):
        # We can create a Deferred, assert that it hasn't fired, then fire it
        # and collect the result.
        deferred = defer.Deferred()
        self.assertThat(deferred, no_result())
        results = []
        deferred.addCallback(results.append)
        marker = object()
        deferred.callback(marker)
        self.assertThat(results, Equals([marker]))

    def test_failure_after_assertion(self):
        # We can create a Deferred, assert that it hasn't fired, then fire it
        # with a failure and collect the result.

        # XXX: Ask Jean-Paul about whether this is good behaviour.
        deferred = defer.Deferred()
        self.assertThat(deferred, no_result())
        results = []
        deferred.addErrback(results.append)
        fail = make_failure(RuntimeError('arbitrary failure'))
        deferred.errback(fail)
        self.assertThat(results, Equals([fail]))


def test_suite():
    from unittest2 import TestLoader, TestSuite
    return TestLoader().loadTestsFromName(__name__)
