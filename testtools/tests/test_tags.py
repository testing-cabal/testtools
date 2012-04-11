# Copyright (c) 2012 testtools developers. See LICENSE for details.

"""Test tag support."""


from testtools import TestCase
from testtools import tags


class TestTags(TestCase):

    def test_no_tags(self):
        tag_context = tags.new_tag_context()
        self.assertEqual(set(), tags.get_current_tags(tag_context))

    def test_add_tag(self):
        tag_context = tags.new_tag_context()
        tag_context = tags.change_tags(tag_context, set(['foo']), set())
        self.assertEqual(set(['foo']), tags.get_current_tags(tag_context))

    def test_add_tag_twice(self):
        tag_context = tags.new_tag_context()
        tag_context = tags.change_tags(tag_context, set(['foo']), set())
        tag_context = tags.change_tags(tag_context, set(['bar']), set())
        self.assertEqual(
            set(['foo', 'bar']), tags.get_current_tags(tag_context))

    def test_remove_tag(self):
        tag_context = tags.new_tag_context()
        tag_context = tags.change_tags(tag_context, set(['foo']), set())
        tag_context = tags.change_tags(tag_context, set(), set(['foo']))
        self.assertEqual(set(), tags.get_current_tags(tag_context))

    def test_child_context(self):
        parent = tags.new_tag_context()
        parent = tags.change_tags(parent, set(['foo']), set())
        child = tags.new_tag_context(parent)
        self.assertEqual(
            tags.get_current_tags(parent), tags.get_current_tags(child))

    def test_add_to_child(self):
        parent = tags.new_tag_context()
        parent = tags.change_tags(parent, set(['foo']), set())
        child = tags.new_tag_context(parent)
        child = tags.change_tags(child, set(['bar']), set())
        self.assertEqual(set(['foo', 'bar']), tags.get_current_tags(child))
        self.assertEqual(set(['foo']), tags.get_current_tags(parent))

    def test_remove_in_child(self):
        parent = tags.new_tag_context()
        parent = tags.change_tags(parent, set(['foo']), set())
        child = tags.new_tag_context(parent)
        child = tags.change_tags(child, set(), set(['foo']))
        self.assertEqual(set(), tags.get_current_tags(child))
        self.assertEqual(set(['foo']), tags.get_current_tags(parent))

    def test_get_parent_context(self):
        parent = tags.new_tag_context()
        parent = tags.change_tags(parent, set(['foo']), set())
        child = tags.new_tag_context(parent)
        child = tags.change_tags(child, set(), set(['foo']))
        child_parent = tags.get_parent_context(child)
        self.assertEqual(parent, child_parent)


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
