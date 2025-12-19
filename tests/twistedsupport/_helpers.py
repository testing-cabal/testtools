# Copyright (c) 2010, 2016 testtools developers. See LICENSE for details.

__all__ = [
    "NeedsTwistedTestCase",
]

from typing import TYPE_CHECKING

from testtools import TestCase

if TYPE_CHECKING:
    from types import ModuleType

    defer: ModuleType | None
else:
    try:
        from twisted.internet import defer
    except ImportError:
        defer = None


class NeedsTwistedTestCase(TestCase):
    def setUp(self):
        super().setUp()
        if defer is None:
            self.skipTest("Need Twisted to run")
