# Copyright (c) 2016 testtools developers. See LICENSE for details.

from testtools import TestCase
from testtools.matchers import Not, always, never


class Test_ConstantMatches(TestCase):
    def test_always(self):
        self.assertThat(object(), always())

    def test_never(self):
        self.assertThat(object(), Not(never()))


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
