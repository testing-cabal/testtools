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
