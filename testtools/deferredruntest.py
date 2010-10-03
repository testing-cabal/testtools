# Copyright (c) 2010 Jonathan M. Lange. See LICENSE for details.

"""Individual test case execution for tests that return Deferreds."""

__all__ = [
    'SynchronousDeferredRunTest',
    ]

from testtools.runtest import RunTest

from twisted.internet import defer


def extract_result(deferred):
    """Extract the result from a fired deferred.

    It can happen that you have an API that returns Deferreds for
    compatibility with Twisted code, but is in fact synchronous, i.e. the
    Deferreds it returns have always fired by the time it returns.  In this
    case, you can use this function to convert the result back into the usual
    form for a synchronous API, i.e. the result itself or a raised exception.

    It would be very bad form to use this as some way of checking if a
    Deferred has fired.
    """
    failures = []
    successes = []
    deferred.addCallbacks(successes.append, failures.append)
    if len(failures) == 1:
        failures[0].raiseException()
    elif len(successes) == 1:
        return successes[0]
    else:
        raise AssertionError("%r has not fired yet." % (deferred,))


class SynchronousDeferredRunTest(RunTest):

    def _run_user(self, function, *args):
        d = defer.maybeDeferred(function, *args)
        def got_exception(failure):
            e = failure.value
            for exc_class, handler in self.handlers:
                if isinstance(e, exc_class):
                    self._exceptions.append(e)
                    return self.exception_caught
            return failure
        d.addErrback(got_exception)
        # XXX: Cheat!
        result = extract_result(d)
        return result
