# Copyright (c) 2008-2015 testtools developers. See LICENSE for details.

"""Compatibility support for python 2 and 3."""

__metaclass__ = type
__all__ = [
    '_b',
    '_u',
    'advance_iterator',
    'BytesIO',
    'classtypes',
    'istext',
    'str_is_unicode',
    'StringIO',
    'reraise',
    'unicode_output_stream',
    'text_or_bytes',
    ]

import codecs
import io
import locale
import os
import re
import sys
import traceback
import unicodedata

from extras import try_import, try_imports

BytesIO = try_imports(['StringIO.StringIO', 'io.BytesIO'])
StringIO = try_imports(['StringIO.StringIO', 'io.StringIO'])
# To let setup.py work, make this a conditional import.
linecache = try_import('linecache2')

try:
    from testtools import _compat2x as _compat
except SyntaxError:
    from testtools import _compat3x as _compat

reraise = _compat.reraise


__u_doc = """A function version of the 'u' prefix.

This is needed becayse the u prefix is not usable in Python 3 but is required
in Python 2 to get a unicode object.

To migrate code that was written as u'\u1234' in Python 2 to 2+3 change
it to be _u('\u1234'). The Python 3 interpreter will decode it
appropriately and the no-op _u for Python 3 lets it through, in Python
2 we then call unicode-escape in the _u function.
"""

if sys.version_info > (3, 0):
    import builtins
    def _u(s):
        return s
    _r = ascii
    def _b(s):
        """A byte literal."""
        return s.encode("latin-1")
    advance_iterator = next
    # GZ 2011-08-24: Seems istext() is easy to misuse and makes for bad code.
    def istext(x):
        return isinstance(x, str)
    def classtypes():
        return (type,)
    str_is_unicode = True
    text_or_bytes = (str, bytes)
else:
    import __builtin__ as builtins
    def _u(s):
        # The double replace mangling going on prepares the string for
        # unicode-escape - \foo is preserved, \u and \U are decoded.
        return (s.replace("\\", "\\\\").replace("\\\\u", "\\u")
            .replace("\\\\U", "\\U").decode("unicode-escape"))
    _r = repr
    def _b(s):
        return s
    advance_iterator = lambda it: it.next()
    def istext(x):
        return isinstance(x, basestring)
    def classtypes():
        import types
        return (type, types.ClassType)
    str_is_unicode = sys.platform == "cli"
    text_or_bytes = (unicode, str)

_u.__doc__ = __u_doc


# GZ 2011-08-24: Using isinstance checks like this encourages bad interfaces,
#                there should be better ways to write code needing this.
if not issubclass(getattr(builtins, "bytes", str), str):
    def _isbytes(x):
        return isinstance(x, bytes)
else:
    # Never return True on Pythons that provide the name but not the real type
    def _isbytes(x):
        return False


def _slow_escape(text):
    """Escape unicode ``text`` leaving printable characters unmodified

    The behaviour emulates the Python 3 implementation of repr, see
    unicode_repr in unicodeobject.c and isprintable definition.

    Because this iterates over the input a codepoint at a time, it's slow, and
    does not handle astral characters correctly on Python builds with 16 bit
    rather than 32 bit unicode type.
    """
    output = []
    for c in text:
        o = ord(c)
        if o < 256:
            if o < 32 or 126 < o < 161:
                output.append(c.encode("unicode-escape"))
            elif o == 92:
                # Separate due to bug in unicode-escape codec in Python 2.4
                output.append("\\\\")
            else:
                output.append(c)
        else:
            # To get correct behaviour would need to pair up surrogates here
            if unicodedata.category(c)[0] in "CZ":
                output.append(c.encode("unicode-escape"))
            else:
                output.append(c)
    return "".join(output)


def text_repr(text, multiline=None):
    """Rich repr for ``text`` returning unicode, triple quoted if ``multiline``.
    """
    is_py3k = sys.version_info > (3, 0)
    nl = _isbytes(text) and bytes((0xA,)) or "\n"
    if multiline is None:
        multiline = nl in text
    if not multiline and (is_py3k or not str_is_unicode and type(text) is str):
        # Use normal repr for single line of unicode on Python 3 or bytes
        return repr(text)
    prefix = repr(text[:0])[:-2]
    if multiline:
        # To escape multiline strings, split and process each line in turn,
        # making sure that quotes are not escaped.
        if is_py3k:
            offset = len(prefix) + 1
            lines = []
            for l in text.split(nl):
                r = repr(l)
                q = r[-1]
                lines.append(r[offset:-1].replace("\\" + q, q))
        elif not str_is_unicode and isinstance(text, str):
            lines = [l.encode("string-escape").replace("\\'", "'")
                for l in text.split("\n")]
        else:
            lines = [_slow_escape(l) for l in text.split("\n")]
        # Combine the escaped lines and append two of the closing quotes,
        # then iterate over the result to escape triple quotes correctly.
        _semi_done = "\n".join(lines) + "''"
        p = 0
        while True:
            p = _semi_done.find("'''", p)
            if p == -1:
                break
            _semi_done = "\\".join([_semi_done[:p], _semi_done[p:]])
            p += 2
        return "".join([prefix, "'''\\\n", _semi_done, "'"])
    escaped_text = _slow_escape(text)
    # Determine which quote character to use and if one gets prefixed with a
    # backslash following the same logic Python uses for repr() on strings
    quote = "'"
    if "'" in text:
        if '"' in text:
            escaped_text = escaped_text.replace("'", "\\'")
        else:
            quote = '"'
    return "".join([prefix, quote, escaped_text, quote])


def unicode_output_stream(stream):
    """Get wrapper for given stream that writes any unicode without exception

    Characters that can't be coerced to the encoding of the stream, or 'ascii'
    if valid encoding is not found, will be replaced. The original stream may
    be returned in situations where a wrapper is determined unneeded.

    The wrapper only allows unicode to be written, not non-ascii bytestrings,
    which is a good thing to ensure sanity and sanitation.
    """
    if (sys.platform == "cli" or
        isinstance(stream, (io.TextIOWrapper, io.StringIO))):
        # Best to never encode before writing in IronPython, or if it is
        # already a TextIO [which in the io library has no encoding
        # attribute).
        return stream
    try:
        writer = codecs.getwriter(stream.encoding or "")
    except (AttributeError, LookupError):
        return codecs.getwriter("ascii")(stream, "replace")
    if writer.__module__.rsplit(".", 1)[1].startswith("utf"):
        # The current stream has a unicode encoding so no error handler is needed
        if sys.version_info > (3, 0):
            return stream
        return writer(stream)
    if sys.version_info > (3, 0):
        # Python 3 doesn't seem to make this easy, handle a common case
        try:
            return stream.__class__(stream.buffer, stream.encoding, "replace",
                stream.newlines, stream.line_buffering)
        except AttributeError:
            pass
    return writer(stream, "replace")
def _get_exception_encoding():
    """Return the encoding we expect messages from the OS to be encoded in"""
    if os.name == "nt":
        # GZ 2010-05-24: Really want the codepage number instead, the error
        #                handling of standard codecs is more deterministic
        return "mbcs"
    # GZ 2010-05-23: We need this call to be after initialisation, but there's
    #                no benefit in asking more than once as it's a global
    #                setting that can change after the message is formatted.
    return locale.getlocale(locale.LC_MESSAGES)[1] or "ascii"


