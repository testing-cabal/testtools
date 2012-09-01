# Copyright (c) 2008-2012 testtools developers. See LICENSE for details.

"""All the matchers.

Matchers, a way to express complex assertions outside the testcase.

Inspired by 'hamcrest'.

Matcher provides the abstract API that all matchers need to implement.

Bundled matchers are listed in __all__: a list can be obtained by running
$ python -c 'import testtools.matchers; print testtools.matchers.__all__'
"""

__all__ = [
    'AfterPreprocessing',
    'AllMatch',
    'Annotate',
    'Contains',
    'ContainsAll',
    'DirExists',
    'DocTestMatches',
    'EndsWith',
    'Equals',
    'FileContains',
    'FileExists',
    'GreaterThan',
    'HasPermissions',
    'Is',
    'IsInstance',
    'KeysEqual',
    'LessThan',
    'MatchesAll',
    'MatchesAny',
    'MatchesException',
    'MatchesListwise',
    'MatchesPredicate',
    'MatchesRegex',
    'MatchesSetwise',
    'MatchesStructure',
    'NotEquals',
    'Not',
    'PathExists',
    'Raises',
    'raises',
    'SamePath',
    'StartsWith',
    'TarballContains',
    ]

from ._core import (
    AfterPreprocessing,
    AllMatch,
    Annotate,
    Contains,
    ContainsAll,
    DirExists,
    DocTestMatches,
    EndsWith,
    Equals,
    FileContains,
    FileExists,
    GreaterThan,
    HasPermissions,
    Is,
    IsInstance,
    KeysEqual,
    LessThan,
    MatchesAll,
    MatchesAny,
    MatchesException,
    MatchesListwise,
    MatchesPredicate,
    MatchesRegex,
    MatchesSetwise,
    MatchesStructure,
    NotEquals,
    Not,
    PathExists,
    Raises,
    raises,
    SamePath,
    StartsWith,
    TarballContains,
    )

# XXX: Compatibility imports.
from ._core import (
    AnnotatedMismatch,
    _BinaryMismatch,
    ContainedByDict,
    ContainsDict,
    DirContains,
    DoesNotEndWith,
    DoesNotStartWith,
    Matcher,
    MatchesAllDict,
    MatchesDict,
    Mismatch,
    MismatchDecorator,
    MismatchError,
    SameMembers,
    _SubDictOf,
    )
