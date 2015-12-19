# Copyright (c) 2008-2015 testtools developers. See LICENSE for details.

import os
import shutil
import tarfile
import tempfile

from testtools import TestCase
from testtools.compat import _u
from testtools.matchers import (
    Contains,
    DocTestMatches,
    Equals,
    )
from testtools.matchers._filesystem import (
    DirContains,
    DirExists,
    FileContains,
    FileExists,
    HasPermissions,
    PathExists,
    SamePath,
    TarballContains,
    )
from .helpers import TestMatchersInterface


class PathHelpers(object):

    def mkdtemp(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        return directory

    def create_file(self, filename, contents=''):
        fp = open(filename, 'w')
        try:
            fp.write(contents)
        finally:
            fp.close()
        self.addCleanup(os.unlink, filename)
        return filename

    def touch(self, filename):
        return self.create_file(filename)


class TestPathExists(TestCase, PathHelpers, TestMatchersInterface):

    def setUp(self):
        super(TestPathExists, self).setUp()
        existing_path = self.mkdtemp()
        nonexisting_path = os.path.join(existing_path, 'doesntexist')

        self.matches_matcher = PathExists()
        self.matches_matches = [existing_path]
        self.matches_mismatches = [nonexisting_path]
        self.str_examples = []
        self.describe_examples = [
            (_u("%s does not exist.") % nonexisting_path,
             nonexisting_path, PathExists()),
        ]


class TestDirExists(TestCase, PathHelpers, TestMatchersInterface):

    def setUp(self):
        super(TestDirExists, self).setUp()
        existing_dir = self.mkdtemp()
        nonexisting_path = os.path.join(existing_dir, 'doesntexist')
        existing_file = self.touch(os.path.join(existing_dir, 'file'))

        self.matches_matcher = DirExists()
        self.matches_matches = [existing_dir]
        self.matches_mismatches = [nonexisting_path, existing_file]
        self.str_examples = []
        self.describe_examples = [
            (PathExists().match(nonexisting_path).describe(),
             nonexisting_path, DirExists()),
            (_u("%s is not a directory.") % existing_file,
             existing_file, DirExists()),
        ]


class TestFileExists(TestCase, PathHelpers, TestMatchersInterface):

    def setUp(self):
        super(TestFileExists, self).setUp()
        existing_dir = self.mkdtemp()
        nonexisting_path = os.path.join(existing_dir, 'doesntexist')
        existing_file = self.touch(os.path.join(existing_dir, 'file'))

        self.matches_matcher = FileExists()
        self.matches_matches = [existing_file]
        self.matches_mismatches = [nonexisting_path, existing_dir]
        self.str_examples = []
        self.describe_examples = [
            (PathExists().match(nonexisting_path).describe(),
             nonexisting_path, FileExists()),
            (_u("%s is not a file.") % existing_dir,
             existing_dir, FileExists()),
        ]


class TestDirContains(TestCase, PathHelpers, TestMatchersInterface):

    def setUp(self):
        super(TestDirContains, self).setUp()
        existing_dir = self.mkdtemp()
        nonexisting_path = os.path.join(existing_dir, 'doesntexist')
        foo = self.touch(os.path.join(existing_dir, 'foo'))
        bar = self.touch(os.path.join(existing_dir, 'bar'))

        self.matches_matcher = DirContains(['foo', 'bar'])
        self.matches_matches = [existing_dir]
        self.matches_mismatches = [nonexisting_path, foo, bar]
        self.str_examples = []
        self.describe_examples = [
            (PathExists().match(nonexisting_path).describe(),
             nonexisting_path, DirContains([])),
            (_u("%s is not a directory.") % (foo,),
             foo, DirContains([])),
        ]

    def test_empty(self):
        tempdir = self.mkdtemp()
        self.assertThat(tempdir, DirContains([]))

    def test_matcher(self):
        tempdir = self.mkdtemp()
        self.touch(os.path.join(tempdir, 'foo'))
        self.touch(os.path.join(tempdir, 'bar'))
        self.assertThat(tempdir, DirContains(matcher=Contains('bar')))

    def test_neither_specified(self):
        self.assertRaises(AssertionError, DirContains)

    def test_both_specified(self):
        self.assertRaises(
            AssertionError, DirContains, filenames=[], matcher=Contains('a'))

    def test_does_not_contain_files(self):
        tempdir = self.mkdtemp()
        self.touch(os.path.join(tempdir, 'foo'))
        mismatch = DirContains(['bar', 'foo']).match(tempdir)
        self.assertThat(
            Equals(['bar', 'foo']).match(['foo']).describe(),
            Equals(mismatch.describe()))


class TestFileContains(TestCase, PathHelpers, TestMatchersInterface):

    def setUp(self):
        super(TestFileContains, self).setUp()
        tempdir = self.mkdtemp()
        nonexisting_path = os.path.join(tempdir, 'doesntexist')
        filepath = self.create_file(
            os.path.join(tempdir, 'foo'), 'Hello World!')
        empty = self.touch(os.path.join(tempdir, 'bar'))

        self.matches_matcher = FileContains('Hello World!')
        self.matches_matches = [filepath]
        self.matches_mismatches = [nonexisting_path, empty]
        self.str_examples = []
        self.describe_examples = [
            (PathExists().match(nonexisting_path).describe(),
             nonexisting_path, FileContains('')),
            (Equals('Hello World!').match('').describe(),
             empty, FileContains('Hello World!')),
        ]

    def test_matcher(self):
        tempdir = self.mkdtemp()
        filename = os.path.join(tempdir, 'foo')
        self.create_file(filename, 'Hello World!')
        self.assertThat(
            filename, FileContains(matcher=DocTestMatches('Hello World!')))

    def test_neither_specified(self):
        self.assertRaises(AssertionError, FileContains)

    def test_both_specified(self):
        self.assertRaises(
            AssertionError, FileContains, contents=[], matcher=Contains('a'))


class TestTarballContains(TestCase, PathHelpers, TestMatchersInterface):

    def setUp(self):
        super(TestTarballContains, self).setUp()
        tarball_a = self._make_tarball(['a', 'b'])
        tarball_b = self._make_tarball(['c', 'd'])

        self.matches_matcher = TarballContains(['a', 'b'])
        self.matches_matches = [tarball_a]
        self.matches_mismatches = [tarball_b]
        self.str_examples = []
        self.describe_examples = [
            (Equals(['c', 'd']).match(['a', 'b']).describe(),
             tarball_a, TarballContains(['c', 'd'])),
        ]

    def _make_tarball(self, files):
        tempdir = self.mkdtemp()
        abs_files = [os.path.join(tempdir, filename) for filename in files]
        for filename in abs_files:
            self.touch(filename)
        new_tmpdir = self.mkdtemp()
        tar_path = os.path.join(new_tmpdir, 'foo.tar.gz')
        tarball = tarfile.open(tar_path, 'w')
        for filename, base in zip(abs_files, files):
            tarball.add(filename, base)
        tarball.close()
        return tar_path


class TestSamePath(TestCase, PathHelpers, TestMatchersInterface):

    def setUp(self):
        super(TestSamePath, self).setUp()
        self.matches_matcher = SamePath('foo')
        self.matches_matches = [
            'foo', 'foo/../foo', 'foo/bar/../', os.path.abspath('foo')]
        self.matches_mismatches = ['bar']
        self.str_examples = []
        self.describe_examples = []

    def test_same_string(self):
        self.assertThat('foo', SamePath('foo'))

    def test_relative_and_absolute(self):
        path = 'foo'
        abspath = os.path.abspath(path)
        self.assertThat(path, SamePath(abspath))
        self.assertThat(abspath, SamePath(path))

    def test_real_path(self):
        tempdir = self.mkdtemp()
        source = os.path.join(tempdir, 'source')
        self.touch(source)
        target = os.path.join(tempdir, 'target')
        try:
            os.symlink(source, target)
        except (AttributeError, NotImplementedError):
            self.skip("No symlink support")
        self.assertThat(source, SamePath(target))
        self.assertThat(target, SamePath(source))


class TestHasPermissions(TestCase, PathHelpers, TestMatchersInterface):

    def setUp(self):
        super(TestHasPermissions, self).setUp()

        tempdir = self.mkdtemp()
        file1 = self.touch(os.path.join(tempdir, 'file1'))
        os.chmod(file1, 0777)
        file2 = self.touch(os.path.join(tempdir, 'file2'))
        os.chmod(file2, 0644)

        self.matches_matcher = HasPermissions('0777')
        self.matches_matches = [file1]
        self.matches_mismatches = [file2]
        self.str_examples = []
        self.describe_examples = [
            (Equals('0777').match('0644').describe(),
             file2, HasPermissions('0777')),
        ]

    def test_match(self):
        tempdir = self.mkdtemp()
        filename = os.path.join(tempdir, 'filename')
        self.touch(filename)
        permissions = oct(os.stat(filename).st_mode)[-4:]
        self.assertThat(filename, HasPermissions(permissions))


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
