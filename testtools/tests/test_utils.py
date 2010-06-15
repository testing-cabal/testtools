# Copyright (c) 2010 testtools developers. See LICENSE for details.

"""Tests for miscellaneous compatibility functions"""

import linecache
import os
import sys
import tempfile
import traceback

import testtools

from testtools.utils import (
    _b,
    _detect_encoding,
    _get_source_encoding,
    )


class TestDetectEncoding(testtools.TestCase):
    """Test detection of Python source encodings"""

    def _check_encoding(self, expected, lines):
        """Check lines are valid Python and encoding is as expected"""
        compile(_b("".join(lines)), "<str>", "exec")
        encoding = _detect_encoding(lines)
        self.assertEqual(expected, encoding,
            "Encoding %r expected but got %r from lines %r" %
                (expected, encoding, lines))

    def test_examples_from_pep(self):
        """Check the examples given in PEP 263 all work as specified

        See 'Examples' section of <http://www.python.org/dev/peps/pep-0263/>
        """
        # With interpreter binary and using Emacs style file encoding comment:
        self._check_encoding("latin-1", (
            "#!/usr/bin/python\n",
            "# -*- coding: latin-1 -*-\n",
            "import os, sys\n"))
        self._check_encoding("iso-8859-15", (
            "#!/usr/bin/python\n",
            "# -*- coding: iso-8859-15 -*-\n",
            "import os, sys\n"))
        self._check_encoding("ascii", (
            "#!/usr/bin/python\n",
            "# -*- coding: ascii -*-\n",
            "import os, sys\n"))
        # Without interpreter line, using plain text:
        self._check_encoding("utf-8", (
            "# This Python file uses the following encoding: utf-8\n",
            "import os, sys\n"))
        # Text editors might have different ways of defining the file's
        # encoding, e.g.
        self._check_encoding("latin-1", (
            "#!/usr/local/bin/python\n",
            "# coding: latin-1\n",
            "import os, sys\n"))
        # Without encoding comment, Python's parser will assume ASCII text:
        self._check_encoding("ascii", (
            "#!/usr/local/bin/python\n",
            "import os, sys\n"))
        # Encoding comments which don't work:
        #   Missing "coding:" prefix:
        self._check_encoding("ascii", (
            "#!/usr/local/bin/python\n",
            "# latin-1\n",
            "import os, sys\n"))
        #   Encoding comment not on line 1 or 2:
        self._check_encoding("ascii", (
            "#!/usr/local/bin/python\n",
            "#\n",
            "# -*- coding: latin-1 -*-\n",
            "import os, sys\n"))
        #   Unsupported encoding:
        #     Correct behaviour is a SyntaxError, which we aren't testing for
        #     and fails instead with MemoryError on Python 2.4
        # self._check_encoding("ascii", (
        #     "#!/usr/local/bin/python\n",
        #     "# -*- coding: utf-42 -*-\n",
        #     "import os, sys\n"))

    def test_bom(self):
        """Test the UTF-8 BOM counts as an encoding declaration"""
        self._check_encoding("utf-8", (
            "\xef\xbb\xbfimport sys\n",
            ))
        self._check_encoding("utf-8", (
            "\xef\xbb\xbf# File encoding: UTF-8\n",
            ))
        self._check_encoding("utf-8", (
            '\xef\xbb\xbf"""Module docstring\n',
            '\xef\xbb\xbfThat should just be a ZWNB"""\n'))
        self._check_encoding("latin-1", (
            '"""Is this coding: latin-1 or coding: utf-8 instead?\n',
            '\xef\xbb\xbfThose should be latin-1 bytes"""\n'))
        self._check_encoding("utf-8", (
            "\xef\xbb\xbf# Is the coding: utf-8 or coding: euc-jp instead?\n",
            '"""Module docstring say \xe2\x98\x86"""\n'))

    def test_multiple_coding_comments(self):
        """Test only the first of multiple coding declarations counts"""
        self._check_encoding("iso-8859-1", (
            "# Is the coding: iso-8859-1\n",
            "# Or is it coding: iso-8859-2\n"))
        self._check_encoding("iso-8859-1", (
            "#!/usr/bin/python\n",
            "# Is the coding: iso-8859-1\n",
            "# Or is it coding: iso-8859-2\n"))
        self._check_encoding("iso-8859-1", (
            "# Is the coding: iso-8859-1 or coding: iso-8859-2\n",
            "# Or coding: iso-8859-3 or coding: iso-8859-4\n"))
        self._check_encoding("iso-8859-2", (
            "# Is the coding iso-8859-1 or coding: iso-8859-2\n",
            "# Spot the missing colon above\n"))


class TestGetSourceEncoding(testtools.TestCase):
    """Test reading and caching the encodings of source files"""

    def setUp(self):
        testtools.TestCase.setUp(self)
        dir = tempfile.mkdtemp()
        self.addCleanup(os.rmdir, dir)
        self.filename = os.path.join(dir, self.id().rsplit(".", 1)[1] + ".py")
        self._written = False

    def put_source(self, text):
        f = open(self.filename, "w")
        try:
            f.write(text)
        finally:
            f.close()
            if not self._written:
                self._written = True
                self.addCleanup(os.remove, self.filename)
                self.addCleanup(linecache.cache.pop, self.filename, None)

    def test_nonexistant_file_as_ascii(self):
        """When file can't be found, the encoding should default to ascii"""
        self.assertEquals("ascii", _get_source_encoding(self.filename))

    def test_encoding_is_cached(self):
        """The encoding should stay the same if the cache isn't invalidated"""
        self.put_source(
            "# coding: iso-8859-13\n"
            "import os\n")
        self.assertEquals("iso-8859-13", _get_source_encoding(self.filename))
        self.put_source(
            "# coding: rot-13\n"
            "vzcbeg bf\n")
        self.assertEquals("iso-8859-13", _get_source_encoding(self.filename))

    def test_traceback_rechecks_encoding(self):
        """A traceback function checks the cache and resets the encoding"""
        self.put_source(
            "# coding: iso-8859-8\n"
            "import os\n")
        self.assertEquals("iso-8859-8", _get_source_encoding(self.filename))
        self.put_source(
            "# coding: utf-8\n"
            "import os\n")
        try:
            exec (compile("raise RuntimeError\n", self.filename, "exec"))
        except RuntimeError:
            traceback.extract_tb(sys.exc_info()[2])
        else:
            self.fail("RuntimeError not raised")
        self.assertEquals("utf-8", _get_source_encoding(self.filename))


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
