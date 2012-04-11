# Copyright (c) 2012 testtools developers. See LICENSE for details.

"""Tag support."""


def new_tag_context(parent=None):
    if parent is None:
        return [set()]
    new_context = list(parent)
    new_context.append(set(parent[-1]))
    return new_context


def get_current_tags(tag_context):
    return set(tag_context[-1])


def get_parent_context(tag_context):
    return list(tag_context[:-1])


def change_tags(tag_context, new_tags, gone_tags):
    tags = set(tag_context[-1])
    tags.update(new_tags)
    tags.difference_update(gone_tags)
    new_context = get_parent_context(tag_context)
    new_context.append(tags)
    return new_context
