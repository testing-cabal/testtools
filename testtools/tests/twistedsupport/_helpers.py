# Copyright (c) 2010, 2016 testtools developers. See LICENSE for details.

__all__ = [
    "NeedsTwistedTestCase",
]

from testtools import TestCase

try:
    from twisted.internet import defer
except ImportError:
    defer = None


class NeedsTwistedTestCase(TestCase):
    def setUp(self):
        super().setUp()
        if defer is None:
            self.skipTest("Need Twisted to run")
