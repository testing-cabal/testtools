# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

__metaclass__ = type
__all__ = [
    'ITestResult',
    ]

from zope.interface import Interface


class ITestResult(Interface):

    def startTest(test):
        """test has started."""

    def stopTest(test):
        """test has stopped."""

    def addError(test, error):
        """got error in test."""

    def addFailure(test, failure):
        """got assertion failure in test."""

    def addSuccess(test):
        """test succeeded."""

    def done():
        """whole run is done."""
