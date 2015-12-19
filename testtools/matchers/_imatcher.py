# Copyright (c) 2015 testtools developers. See LICENSE for details.

"""Interfaces for matchers and mismatches."""


from zope.interface import Interface


class IMatcher(Interface):
    """A pattern matcher, to be used with ``assertThat``."""

    def match(something):
        """Does ``something`` match this matcher?

        If yes, return ``None``. Otherwise, return an ``IMismatch``.
        """

    def __str__():
        """Get a sensible human representation of the matcher.

        This should include the parameters given to the matcher and any
        state that would affect the matches operation.
        """


class IMismatch(Interface):
    """An object describing a mismatch detected by a matcher."""

    def describe():
        """Describe the mismatch.

        This should be human-readable text. i.e. ``unicode`` on Python 2 or
        ``str`` on Python 3.
        """

    def get_details():
        """Get extra details about the mismatch.

        This allows the mismatch to provide extra information beyond the basic
        description, including large text file, binary files and debugging
        internals.

        ``assertThat`` will query ``get_details`` and attach all its values to
        the test, permitting them to be reported in whatever manner the test
        environment chooses.

        :return: a dict mapping names to ``Content`` objects. The name is a
            string to name the detail, and the ``Content`` object is the
            detail to add to the result. For more information see the API to
            which items from this dict are passed
            ``testtools.TestCase.addDetail``.
        """
