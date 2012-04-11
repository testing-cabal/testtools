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


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
