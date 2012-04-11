# Copyright (c) 2012 testtools developers. See LICENSE for details.

"""Tag support."""


class TagContext(object):

    def __init__(self, parent=None):
        self._parent = parent
        self._tags = set()
        if parent:
            self._tags.update(parent.get_current_tags())

    def get_current_tags(self):
        return set(self._tags)

    def get_parent(self):
        return self._parent

    def change_tags(self, new_tags, gone_tags):
        self._tags.update(new_tags)
        self._tags.difference_update(gone_tags)


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
    new_context = list(tag_context)
    new_context[-1].update(new_tags)
    new_context[-1].difference_update(gone_tags)
    return new_context
