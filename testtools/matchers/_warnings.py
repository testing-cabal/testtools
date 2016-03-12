# Copyright (c) 2009-2016 testtools developers. See LICENSE for details.

__all__ = [
    'Warnings',
    'warning_message',
    'is_deprecated']

import warnings

from ._basic import Is
from ._const import Always
from ._datastructures import MatchesListwise, MatchesStructure
from ._higherorder import (
    AfterPreprocessing,
    Annotate,
    MatchesAll,
    Not,
    )
from ._impl import Mismatch


def warning_message(category_type, message=None, filename=None, lineno=None,
                    line=None):
    """
    Create a matcher that will match `warnings.WarningMessage`\s.

    :param category_type: A warning type.
    :param message_matcher: Match the warning message against this.
    :param filename_matcher: Match the warning filename against this.
    :param lineno_matcher: Match the warning line number against this.
    :param line_matcher: Match the warning line of code against this.
    """
    category_matcher = Is(category_type)
    message_matcher = message or Always()
    filename_matcher = filename or Always()
    lineno_matcher = lineno or Always()
    line_matcher = line or Always()
    return MatchesStructure(
        category=Annotate(
            "Warning's category type does not match",
            category_matcher),
        message=Annotate(
            "Warning's message does not match",
            AfterPreprocessing(str, message_matcher)),
        filename=Annotate(
            "Warning's filname does not match",
            filename_matcher),
        lineno=Annotate(
            "Warning's line number does not match",
            lineno_matcher),
        line=Annotate(
            "Warning's source line does not match",
            line_matcher))


class Warnings(object):
    """
    Match if the matchee produces deprecation warnings.
    """
    def __init__(self, warnings_matcher=None):
        """
        Create a Warnings matcher.

        :param warnings_matcher: Optional validator for the warnings emitted by
        matchee. If no warnings_matcher is supplied then the simple fact that
        at least one warning is emitted is considered enough to match on.
        """
        self.warnings_matcher = warnings_matcher

    def match(self, matchee):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            matchee()
            if not w:
                mismatch = Mismatch('Expected at least one warning, got none')
            elif self.warnings_matcher:
                mismatch = self.warnings_matcher.match(w)
            else:
                mismatch = None
            return mismatch

    def __str__(self):
        return 'Warnings({!s})'.format(self.warnings_matcher)


def is_deprecated(message):
    """
    Make a matcher that checks that a callable produces exactly one
    `DeprecationWarning`.

    :param message: Matcher for the warning message.
    """
    return Warnings(
        MatchesListwise([
            warning_message(
                category_type=DeprecationWarning,
                message=message)]))
