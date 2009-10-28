# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Content - a MIME-like Content object."""

from unittest import TestResult

from testtools.content_type import ContentType


class Content(object):
    """A MIME-like Content object.
    
    Content objects can be serialised to bytes using the iter_bytes method.
    If the Content-Type is recognised by other code, they are welcome to 
    look for richer contents that mere byte serialisation - for example in
    memory object graphs etc. However, such code MUST be prepared to receive
    a generic Content object that has been reconstructed from a byte stream.
    
    :ivar content_type: The content type of this Content.
    """

    def __init__(self, content_type, get_bytes):
        """Create a ContentType."""
        if None in (content_type, get_bytes):
            raise ValueError("None not permitted in %r, %r" % (
                content_type, get_bytes))
        self.content_type = content_type
        self._get_bytes = get_bytes

    def __eq__(self, other):
        return (self.content_type == other.content_type and
            ''.join(self.iter_bytes()) == ''.join(other.iter_bytes()))

    def iter_bytes(self):
        """Iterate over bytestrings of the serialised content."""
        return self._get_bytes()

    def __repr__(self):
        return "<Content type=%r, value=%r>" % (
            self.content_type, ''.join(self.iter_bytes()))


class TracebackContent(Content):
    """Content object for tracebacks.

    This adapts an exc_info tuple to the Content interface.
    text/x-traceback;language=python is used for the mime type, in order to
    provide room for other languages to format their tracebacks differently.
    """

    def __init__(self, err, test):
        """Create a TracebackContent for err."""
        if err is None:
            raise ValueError("err may not be None")
        content_type = ContentType('text', 'x-traceback',
            {"language": "python"})
        self._result = TestResult()
        super(TracebackContent, self).__init__(content_type,
            lambda:[self._result._exc_info_to_string(err, test)])
