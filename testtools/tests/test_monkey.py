# Copyright (c) 2010 Twisted Matrix Laboratories.
# See LICENSE for details.

"""Tests for testtools.monkey."""

from testtools import TestCase
from testtools.monkey import MonkeyPatcher


class TestObj:

    def __init__(self):
        self.foo = 'foo value'
        self.bar = 'bar value'
        self.baz = 'baz value'


class MonkeyPatcherTest(TestCase):
    """
    Tests for 'MonkeyPatcher' monkey-patching class.
    """

    def setUp(self):
        super(MonkeyPatcherTest, self).setUp()
        self.test_object = TestObj()
        self.original_object = TestObj()
        self.monkey_patcher = MonkeyPatcher()

    def test_empty(self):
        # A monkey patcher without patches doesn't change a thing.
        self.monkey_patcher.patch()

        # We can't assert that all state is unchanged, but at least we can
        # check our test object.
        self.assertEquals(self.original_object.foo, self.test_object.foo)
        self.assertEquals(self.original_object.bar, self.test_object.bar)
        self.assertEquals(self.original_object.baz, self.test_object.baz)

    def test_constructWithPatches(self):
        # Constructing a 'MonkeyPatcher' with patches adds all of the given
        # patches to the patch list.
        patcher = MonkeyPatcher((self.test_object, 'foo', 'haha'),
                                (self.test_object, 'bar', 'hehe'))
        patcher.patch()
        self.assertEquals('haha', self.test_object.foo)
        self.assertEquals('hehe', self.test_object.bar)
        self.assertEquals(self.original_object.baz, self.test_object.baz)

    def test_patchExisting(self):
        # Patching an attribute that exists sets it to the value defined in the
        # patch.
        self.monkey_patcher.addPatch(self.test_object, 'foo', 'haha')
        self.monkey_patcher.patch()
        self.assertEquals(self.test_object.foo, 'haha')

    def test_patchNonExisting(self):
        # Patching a non-existing attribute fails with an AttributeError.
        self.monkey_patcher.addPatch(self.test_object, 'nowhere',
                                    'blow up please')
        self.assertRaises(AttributeError, self.monkey_patcher.patch)

    def test_patchAlreadyPatched(self):
        # Adding a patch for an object and attribute that already have a patch
        # overrides the existing patch.
        self.monkey_patcher.addPatch(self.test_object, 'foo', 'blah')
        self.monkey_patcher.addPatch(self.test_object, 'foo', 'BLAH')
        self.monkey_patcher.patch()
        self.assertEquals(self.test_object.foo, 'BLAH')
        self.monkey_patcher.restore()
        self.assertEquals(self.test_object.foo, self.original_object.foo)

    def test_restoreTwiceIsANoOp(self):
        # Restoring an already-restored monkey patch is a no-op.
        self.monkey_patcher.addPatch(self.test_object, 'foo', 'blah')
        self.monkey_patcher.patch()
        self.monkey_patcher.restore()
        self.assertEquals(self.test_object.foo, self.original_object.foo)
        self.monkey_patcher.restore()
        self.assertEquals(self.test_object.foo, self.original_object.foo)

    def test_runWithPatchesDecoration(self):
        # runWithPatches runs the given callable, passing in all arguments and
        # keyword arguments, and returns the return value of the callable.
        log = []

        def f(a, b, c=None):
            log.append((a, b, c))
            return 'foo'

        result = self.monkey_patcher.runWithPatches(f, 1, 2, c=10)
        self.assertEquals('foo', result)
        self.assertEquals([(1, 2, 10)], log)

    def test_repeatedRunWithPatches(self):
        # We can call the same function with runWithPatches more than
        # once. All patches apply for each call.
        def f():
            return (self.test_object.foo, self.test_object.bar,
                    self.test_object.baz)

        self.monkey_patcher.addPatch(self.test_object, 'foo', 'haha')
        result = self.monkey_patcher.runWithPatches(f)
        self.assertEquals(
            ('haha', self.original_object.bar, self.original_object.baz),
            result)
        result = self.monkey_patcher.runWithPatches(f)
        self.assertEquals(
            ('haha', self.original_object.bar, self.original_object.baz),
            result)

    def test_runWithPatchesRestores(self):
        # runWithPatches restores the original values after the function has
        # executed.
        self.monkey_patcher.addPatch(self.test_object, 'foo', 'haha')
        self.assertEquals(self.original_object.foo, self.test_object.foo)
        self.monkey_patcher.runWithPatches(lambda: None)
        self.assertEquals(self.original_object.foo, self.test_object.foo)

    def test_runWithPatchesRestoresOnException(self):
        # runWithPatches restores the original values even when the function
        # raises an exception.
        def _():
            self.assertEquals(self.test_object.foo, 'haha')
            self.assertEquals(self.test_object.bar, 'blahblah')
            raise RuntimeError, "Something went wrong!"

        self.monkey_patcher.addPatch(self.test_object, 'foo', 'haha')
        self.monkey_patcher.addPatch(self.test_object, 'bar', 'blahblah')

        self.assertRaises(RuntimeError, self.monkey_patcher.runWithPatches, _)
        self.assertEquals(self.test_object.foo, self.original_object.foo)
        self.assertEquals(self.test_object.bar, self.original_object.bar)


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
