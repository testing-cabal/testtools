from testtools.matchers import (
    Annotate,
    MismatchError,
    )


def assert_that(matchee, matcher, message='', verbose=False):
    """Assert that matchee is matched by matcher.

    This should only be used when you need to use a function-based matcher,
    ``assertThat`` in :py:class:`testtools.TestCase` is prefered and has more
    features.

    :param matchee: An object to match with ``matcher``.
    :param IMatcher matcher: An object meeting the testtools.Matcher protocol.
    :raises MismatchError: When ``matcher`` does not match ``matchee``.

    """
    matcher = Annotate.if_message(message, matcher)
    mismatch = matcher.match(matchee)
    if not mismatch:
        return
    raise MismatchError(matchee, matcher, mismatch, verbose)
