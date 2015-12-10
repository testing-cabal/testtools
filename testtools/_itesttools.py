# Copyright (c) 2015 testtools developers. See LICENSE for details.

from zope.interface import Interface


class IRunnable(Interface):
    """A thing that a test runner can run."""

    def __call__(result=None):
        """Equivalent to ``run``."""

    def countTestCases():
        """Return the number of tests this represents."""

    def debug():
        pass

    def run(result=None):
        """Run the test."""


class ITestCase(IRunnable):
    """An individual test case."""

    def __str__():
        """Return a short, human-readable description."""

    def id():
        """A unique identifier."""

    def shortDescription(self):
        """Return a short, human-readable description."""
