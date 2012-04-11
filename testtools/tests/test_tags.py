# Copyright (c) 2012 testtools developers. See LICENSE for details.

"""Test tag support."""


from testtools import TestCase
from testtools.tags import TagContext


class TestTags(TestCase):

    def test_no_tags(self):
        tag_context = TagContext()
        self.assertEqual(set(), tag_context.get_current_tags())

    def test_add_tag(self):
        tag_context = TagContext()
        tag_context.change_tags(set(['foo']), set())
        self.assertEqual(set(['foo']), tag_context.get_current_tags())

    def test_add_tag_twice(self):
        tag_context = TagContext()
        tag_context.change_tags(set(['foo']), set())
        tag_context.change_tags(set(['bar']), set())
        self.assertEqual(
            set(['foo', 'bar']), tag_context.get_current_tags())

    def test_remove_tag(self):
        tag_context = TagContext()
        tag_context.change_tags(set(['foo']), set())
        tag_context.change_tags(set(), set(['foo']))
        self.assertEqual(set(), tag_context.get_current_tags())

    def test_child_context(self):
        parent = TagContext()
        parent.change_tags(set(['foo']), set())
        child = TagContext(parent)
        self.assertEqual(
            parent.get_current_tags(), child.get_current_tags())

    def test_add_to_child(self):
        parent = TagContext()
        parent.change_tags(set(['foo']), set())
        child = TagContext(parent)
        child.change_tags(set(['bar']), set())
        self.assertEqual(set(['foo', 'bar']), child.get_current_tags())
        self.assertEqual(set(['foo']), parent.get_current_tags())

    def test_remove_in_child(self):
        parent = TagContext()
        parent.change_tags(set(['foo']), set())
        child = TagContext(parent)
        child.change_tags(set(), set(['foo']))
        self.assertEqual(set(), child.get_current_tags())
        self.assertEqual(set(['foo']), parent.get_current_tags())

    def test_get_parent(self):
        parent = TagContext()
        parent.change_tags(set(['foo']), set())
        child = TagContext(parent)
        child.change_tags(set(), set(['foo']))
        self.assertEqual(parent, child.get_parent())


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
