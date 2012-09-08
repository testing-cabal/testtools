# Copyright (c) 2009-2012 testtools developers. See LICENSE for details.

"""Matchers, a way to express complex assertions outside the testcase.

Inspired by 'hamcrest'.

Matcher provides the abstract API that all matchers need to implement.

Bundled matchers are listed in __all__: a list can be obtained by running
$ python -c 'import testtools.matchers; print testtools.matchers.__all__'
"""

__metaclass__ = type
__all__ = [
    'MatchesPredicate',
    ]

from testtools.compat import (
    _isbytes,
    istext,
    str_is_unicode,
    text_repr
    )


class Matcher(object):
    """A pattern matcher.

    A Matcher must implement match and __str__ to be used by
    testtools.TestCase.assertThat. Matcher.match(thing) returns None when
    thing is completely matched, and a Mismatch object otherwise.

    Matchers can be useful outside of test cases, as they are simply a
    pattern matching language expressed as objects.

    testtools.matchers is inspired by hamcrest, but is pythonic rather than
    a Java transcription.
    """

    def match(self, something):
        """Return None if this matcher matches something, a Mismatch otherwise.
        """
        raise NotImplementedError(self.match)

    def __str__(self):
        """Get a sensible human representation of the matcher.

        This should include the parameters given to the matcher and any
        state that would affect the matches operation.
        """
        raise NotImplementedError(self.__str__)


class Mismatch(object):
    """An object describing a mismatch detected by a Matcher."""

    def __init__(self, description=None, details=None):
        """Construct a `Mismatch`.

        :param description: A description to use.  If not provided,
            `Mismatch.describe` must be implemented.
        :param details: Extra details about the mismatch.  Defaults
            to the empty dict.
        """
        if description:
            self._description = description
        if details is None:
            details = {}
        self._details = details

    def describe(self):
        """Describe the mismatch.

        This should be either a human-readable string or castable to a string.
        In particular, is should either be plain ascii or unicode on Python 2,
        and care should be taken to escape control characters.
        """
        try:
            return self._description
        except AttributeError:
            raise NotImplementedError(self.describe)

    def get_details(self):
        """Get extra details about the mismatch.

        This allows the mismatch to provide extra information beyond the basic
        description, including large text or binary files, or debugging internals
        without having to force it to fit in the output of 'describe'.

        The testtools assertion assertThat will query get_details and attach
        all its values to the test, permitting them to be reported in whatever
        manner the test environment chooses.

        :return: a dict mapping names to Content objects. name is a string to
            name the detail, and the Content object is the detail to add
            to the result. For more information see the API to which items from
            this dict are passed testtools.TestCase.addDetail.
        """
        return getattr(self, '_details', {})

    def __repr__(self):
        return  "<testtools.matchers.Mismatch object at %x attributes=%r>" % (
            id(self), self.__dict__)


class MismatchError(AssertionError):
    """Raised when a mismatch occurs."""

    # This class exists to work around
    # <https://bugs.launchpad.net/testtools/+bug/804127>.  It provides a
    # guaranteed way of getting a readable exception, no matter what crazy
    # characters are in the matchee, matcher or mismatch.

    def __init__(self, matchee, matcher, mismatch, verbose=False):
        # Have to use old-style upcalling for Python 2.4 and 2.5
        # compatibility.
        AssertionError.__init__(self)
        self.matchee = matchee
        self.matcher = matcher
        self.mismatch = mismatch
        self.verbose = verbose

    def __str__(self):
        difference = self.mismatch.describe()
        if self.verbose:
            # GZ 2011-08-24: Smelly API? Better to take any object and special
            #                case text inside?
            if istext(self.matchee) or _isbytes(self.matchee):
                matchee = text_repr(self.matchee, multiline=False)
            else:
                matchee = repr(self.matchee)
            return (
                'Match failed. Matchee: %s\nMatcher: %s\nDifference: %s\n'
                % (matchee, self.matcher, difference))
        else:
            return difference

    if not str_is_unicode:

        __unicode__ = __str__

        def __str__(self):
            return self.__unicode__().encode("ascii", "backslashreplace")


class MismatchDecorator(object):
    """Decorate a ``Mismatch``.

    Forwards all messages to the original mismatch object.  Probably the best
    way to use this is inherit from this class and then provide your own
    custom decoration logic.
    """

    def __init__(self, original):
        """Construct a `MismatchDecorator`.

        :param original: A `Mismatch` object to decorate.
        """
        self.original = original

    def __repr__(self):
        return '<testtools.matchers.MismatchDecorator(%r)>' % (self.original,)

    def describe(self):
        return self.original.describe()

    def get_details(self):
        return self.original.get_details()


class MatchesPredicate(Matcher):
    """Match if a given function returns True.

    It is reasonably common to want to make a very simple matcher based on a
    function that you already have that returns True or False given a single
    argument (i.e. a predicate function).  This matcher makes it very easy to
    do so. e.g.::

      IsEven = MatchesPredicate(lambda x: x % 2 == 0, '%s is not even')
      self.assertThat(4, IsEven)
    """

    def __init__(self, predicate, message):
        """Create a ``MatchesPredicate`` matcher.

        :param predicate: A function that takes a single argument and returns
            a value that will be interpreted as a boolean.
        :param message: A message to describe a mismatch.  It will be formatted
            with '%' and be given whatever was passed to ``match()``. Thus, it
            needs to contain exactly one thing like '%s', '%d' or '%f'.
        """
        self.predicate = predicate
        self.message = message

    def __str__(self):
        return '%s(%r, %r)' % (
            self.__class__.__name__, self.predicate, self.message)

    def match(self, x):
        if not self.predicate(x):
            return Mismatch(self.message % x)


# Signal that this is part of the testing framework, and that code from this
# should not normally appear in tracebacks.
__unittest = True
