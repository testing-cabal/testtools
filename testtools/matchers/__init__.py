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
    ContainsAll,
    DocTestMatches,
    KeysEqual,
    MatchesAll,
    MatchesAny,
    MatchesException,
    MatchesListwise,
    MatchesPredicate,
    MatchesRegex,
    MatchesSetwise,
    MatchesStructure,
    Not,
    Raises,
    raises,
    )

from ._basic import (
    Contains,
    EndsWith,
    Equals,
    GreaterThan,
    Is,
    IsInstance,
    LessThan,
    NotEquals,
    StartsWith,
    )
from ._filesystem import (
    DirExists,
    FileContains,
    FileExists,
    HasPermissions,
    PathExists,
    SamePath,
    TarballContains,
    )

# XXX: Compatibility imports.
from ._core import (
    AnnotatedMismatch,
    ContainedByDict,
    ContainsDict,
    Matcher,
    MatchesAllDict,
    MatchesDict,
    Mismatch,
    MismatchDecorator,
    MismatchError,
    _SubDictOf,
    )
from ._filesystem import (
    DirContains,
    )

from ._basic import (
    _BinaryMismatch,
    DoesNotEndWith,
    DoesNotStartWith,
    SameMembers,
    )

# XXX: Probably want to split into:
# - the core system -- what makes matchers tick.
# - standard matchers -- things like equality, endswith etc.
#   - what's a good name for this?  _basic? _fundamental? _python? _common?
#     Just pick one.  Rob will disagree with whatever is picked anyway.
# - matchers that combine other matchers
