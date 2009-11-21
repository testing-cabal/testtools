# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Matchers, a way to express complex assertions outside the testcase.

Inspired by 'hamcrest'.

Matcher provides the abstract API that all matchers need to implement.

Bundled matchers are listed in __all__: a list can be obtained by running
$ python -c 'import testtools.matchers; print testtools.matchers.__all__'
"""

__metaclass__ = type
__all__ = [
    'DocTestMatches',
    ]

import doctest


class Matcher:
    """A pattern matcher.

    A Matcher must implement matches, __str__ and describe_difference to be
    used by testtools.TestCase.assertThat.

    Matchers can be useful outside of test cases, as they are simply a 
    pattern matching language expressed as objects.

    testtools.matchers is inspired by hamcrest, but is pythonic rather than
    a Java transcription.
    """

    def matches(self, something):
        """Returns True if this matcher matches something, False otherwise."""
        raise NotImplementedError(self.matches)

    def __str__(self):
        """Get a sensible human representation of the matcher.
        
        This should include the parameters given to the matcher and any
        state that would affect the matches operation.
        """
        raise NotImplementedError(self.__str__)

    def describe_difference(self, something):
        """Describe why something did not match.
        
        This should be either human readable or castable to a string.
        """
        raise NotImplementedError(self.describe_difference)


class DocTestMatches:
    """See if a string matches a doctest example."""

    def __init__(self, example, flags=0):
        """Create a DocTestMatches to match example.

        :param example: The example to match e.g. 'foo bar baz'
        :param flags: doctest comparison flags to match on. e.g.
            doctest.ELLIPSIS.
        """
        if not example.endswith('\n'):
            example += '\n'
        self.want = example # required variable name by doctest.
        self.flags = flags
        self._checker = doctest.OutputChecker()

    def __str__(self):
        if self.flags:
            flagstr = ", flags=%d" % self.flags
        else:
            flagstr = ""
        return 'DocTestMatches(%r%s)' % (self.want, flagstr)

    def _with_nl(self, actual):
        result = str(actual)
        if not result.endswith('\n'):
            result += '\n'
        return result

    def matches(self, actual):
        return self._checker.check_output(self.want, self._with_nl(actual),
            self.flags)

    def describe_difference(self, actual):
        return self._checker.output_difference(self, self._with_nl(actual),
            self.flags)
