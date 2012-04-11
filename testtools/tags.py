# Copyright (c) 2012 testtools developers. See LICENSE for details.

"""Tag support."""


def new_tag_context(parent=None):
    if parent is None:
        return set()
    return set(parent)


def get_current_tags(tag_context):
    return set(tag_context)


def change_tags(tag_context, new_tags, gone_tags):
    new_context = new_tag_context()
    new_context.update(tag_context)
    new_context.update(new_tags)
    new_context.difference_update(gone_tags)
    return new_context
