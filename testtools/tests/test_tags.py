# Copyright (c) 2012 testtools developers. See LICENSE for details.

"""Test tag support."""


from testtools import TestCase
from testtools import tags


class TestTags(TestCase):

    def new_tag_context(self):
        return tags.new_tag_context()

    def change_tags(self, tag_context, new_tags, gone_tags):
        return tags.change_tags(tag_context, new_tags, gone_tags)

    def get_current_tags(self, tag_context):
        return tags.get_current_tags(tag_context)

    def push_tag_context(self, parent):
        return tags.new_tag_context(parent)

    def pop_tag_context(self, child):
        return tags.get_parent_context(child)

    def test_no_tags(self):
        tag_context = self.new_tag_context()
        self.assertEqual(set(), self.get_current_tags(tag_context))

    def test_add_tag(self):
        tag_context = self.new_tag_context()
        tag_context = self.change_tags(tag_context, set(['foo']), set())
        self.assertEqual(set(['foo']), self.get_current_tags(tag_context))

    def test_add_tag_twice(self):
        tag_context = self.new_tag_context()
        tag_context = self.change_tags(tag_context, set(['foo']), set())
        tag_context = self.change_tags(tag_context, set(['bar']), set())
        self.assertEqual(
            set(['foo', 'bar']), self.get_current_tags(tag_context))

    def test_remove_tag(self):
        tag_context = self.new_tag_context()
        tag_context = self.change_tags(tag_context, set(['foo']), set())
        tag_context = self.change_tags(tag_context, set(), set(['foo']))
        self.assertEqual(set(), self.get_current_tags(tag_context))

    def test_child_context(self):
        parent = self.new_tag_context()
        parent = self.change_tags(parent, set(['foo']), set())
        child = self.push_tag_context(parent)
        self.assertEqual(
            self.get_current_tags(parent), self.get_current_tags(child))

    def test_add_to_child(self):
        parent = self.new_tag_context()
        parent = self.change_tags(parent, set(['foo']), set())
        child = self.push_tag_context(parent)
        child = self.change_tags(child, set(['bar']), set())
        self.assertEqual(set(['foo', 'bar']), self.get_current_tags(child))
        self.assertEqual(set(['foo']), self.get_current_tags(parent))

    def test_remove_in_child(self):
        parent = self.new_tag_context()
        parent = self.change_tags(parent, set(['foo']), set())
        child = self.push_tag_context(parent)
        child = self.change_tags(child, set(), set(['foo']))
        self.assertEqual(set(), self.get_current_tags(child))
        self.assertEqual(set(['foo']), self.get_current_tags(parent))

    def test_pop_tag_context(self):
        parent = self.new_tag_context()
        parent = self.change_tags(parent, set(['foo']), set())
        child = self.push_tag_context(parent)
        child = self.change_tags(child, set(), set(['foo']))
        child_parent = self.pop_tag_context(child)
        self.assertEqual(parent, child_parent)


class TestTagContext(TestTags):

    def new_tag_context(self):
        return tags.TagContext()

    def change_tags(self, tag_context, new_tags, gone_tags):
        tag_context.change_tags(new_tags, gone_tags)
        return tag_context

    def get_current_tags(self, tag_context):
        return tag_context.get_current_tags()

    def push_tag_context(self, parent):
        return tags.TagContext(parent)

    def pop_tag_context(self, child):
        return child.get_parent()


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
