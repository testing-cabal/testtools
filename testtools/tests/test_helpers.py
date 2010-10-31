# Copyright (c) 2010 Jonathan M. Lange. See LICENSE for details.

from testtools import TestCase
from testtools.helpers import try_import
from testtools.matchers import Is


class TestTryImport(TestCase):

    def test_doesnt_exist(self):
        # try_import('thing', foo) returns foo if 'thing' doesn't exist.
        marker = object()
        result = try_import('doesntexist', marker)
        self.assertThat(result, Is(marker))

    def test_None_is_default_alternative(self):
        # try_import('thing') returns None if 'thing' doesn't exist.
        result = try_import('doesntexist')
        self.assertThat(result, Is(None))

    def test_existing_module(self):
        # try_import('thing', foo) imports 'thing' and returns it if it's a
        # module that exists.
        result = try_import('os', object())
        import os
        self.assertThat(result, Is(os))

    def test_existing_submodule(self):
        # try_import('thing', foo) imports 'thing' and returns it if it's a
        # module that exists.
        result = try_import('os.path', object())
        import os
        self.assertThat(result, Is(os.path))


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
