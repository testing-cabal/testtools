from testtools.matchers import (
    Annotate,
    MismatchError,
    )


def assert_that(matchee, matcher, message='', verbose=False):
    matcher = Annotate.if_message(message, matcher)
    mismatch = matcher.match(matchee)
    if not mismatch:
        return
    raise MismatchError(matchee, matcher, mismatch, verbose)
