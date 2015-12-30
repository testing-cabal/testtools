# Copyright (c) testtools developers. See LICENSE for details.

"""Utilities for Deferreds."""


class DeferredNotFired(Exception):
    """Raised when we extract a result from a Deferred that's not fired yet."""

    def __init__(self, deferred):
        super(DeferredNotFired, self).__init__(
            "%r has not fired yet." % (deferred,))


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
        raise DeferredNotFired(deferred)
