from testtools.matchers import (
    Annotate,
    IMatcher,
    IMismatch,
    MismatchError,
)


def assert_that(matchee, matcher, message='', verbose=False):
    """Assert that matchee is matched by matcher.

    This should only be used when you need to use a function based
    matcher, assertThat in Testtools.Testcase is prefered and has more
    features

    :param matchee: An object to match with matcher.
    :param IMatcher matcher: The matcher to match with.
    :raises MismatchError: When matcher does not match thing.
    """
    matcher = Annotate.if_message(message, IMatcher(matcher, matcher))
    mismatch = matcher.match(matchee)
    if not mismatch:
        return
    raise MismatchError(
        matchee, matcher, IMismatch(mismatch, mismatch), verbose)
