# Copyright (c) 2008-2012 testtools developers. See LICENSE for details.

"""Extensions to the standard Python unittest library."""

__all__ = [
    "ConcurrentStreamTestSuite",
    "ConcurrentTestSuite",
    "CopyStreamResult",
    "DecorateTestCaseResult",
    "ErrorHolder",
    "ExpectedException",
    "ExtendedToOriginalDecorator",
    "ExtendedToStreamDecorator",
    "FixtureSuite",
    "MultiTestResult",
    "MultipleExceptions",
    "PlaceHolder",
    "ResourcedToStreamDecorator",
    "RunTest",
    "StreamFailFast",
    "StreamResult",
    "StreamResultRouter",
    "StreamSummary",
    "StreamTagger",
    "StreamToDict",
    "StreamToExtendedDecorator",
    "StreamToQueue",
    "Tagger",
    "TestByTestResult",
    "TestCase",
    "TestControl",
    "TestResult",
    "TestResultDecorator",
    "TextTestResult",
    "ThreadsafeForwardingResult",
    "TimestampingStreamResult",
    "__version__",
    "clone_test_with_new_id",
    "iterate_tests",
    "run_test_with",
    "skip",
    "skipIf",
    "skipUnless",
    "unique_text_generator",
    "version",
]

from testtools.matchers._impl import Matcher  # noqa: F401
from testtools.runtest import (
    MultipleExceptions,
    RunTest,
)
from testtools.testcase import (
    DecorateTestCaseResult,
    ErrorHolder,
    ExpectedException,
    PlaceHolder,
    TestCase,
    clone_test_with_new_id,
    run_test_with,
    skip,
    skipIf,
    skipUnless,
    unique_text_generator,
)
from testtools.testresult import (
    CopyStreamResult,
    ExtendedToOriginalDecorator,
    ExtendedToStreamDecorator,
    MultiTestResult,
    ResourcedToStreamDecorator,
    StreamFailFast,
    StreamResult,
    StreamResultRouter,
    StreamSummary,
    StreamTagger,
    StreamToDict,
    StreamToExtendedDecorator,
    StreamToQueue,
    Tagger,
    TestByTestResult,
    TestControl,
    TestResult,
    TestResultDecorator,
    TextTestResult,
    ThreadsafeForwardingResult,
    TimestampingStreamResult,
)
from testtools.testsuite import (
    ConcurrentStreamTestSuite,
    ConcurrentTestSuite,
    FixtureSuite,
    iterate_tests,
)


def __get_git_version() -> str | None:
    import os
    import subprocess

    cwd = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)

    try:
        out = subprocess.check_output(
            ["git", "describe"], stderr=subprocess.STDOUT, cwd=cwd
        )
    except (OSError, subprocess.CalledProcessError):
        return None

    try:
        version = out.strip().decode("utf-8")
    except UnicodeDecodeError:
        return None

    if "-" in version:  # after tag
        # convert version-N-githash to version.postN+githash
        return version.replace("-", ".post", 1).replace("-g", "+git", 1)
    else:
        return version


# same format as sys.version_info: "A tuple containing the five components of
# the version number: major, minor, micro, releaselevel, and serial. All
# values except releaselevel are integers; the release level is 'alpha',
# 'beta', 'candidate', or 'final'. The version_info value corresponding to the
# Python version 2.0 is (2, 0, 0, 'final', 0)."  Additionally we use a
# releaselevel of 'dev' for unreleased under-development code.
#
# If the releaselevel is 'alpha' then the major/minor/micro components are not
# established at this point, and setup.py will use a version of next-$(revno).
# If the releaselevel is 'final', then the tarball will be major.minor.micro.
# Otherwise it is major.minor.micro~$(revno).

try:
    from ._version import __version__, version
except ModuleNotFoundError:
    # package is not installed
    if v := __get_git_version():
        version = v
        # we're in a git repo
        __version__ = tuple([int(x) if x.isdigit() else x for x in version.split(".")])
    else:
        # we're working with a tarball or similar
        version = "0.0.0"
        __version__ = (0, 0, 0)
