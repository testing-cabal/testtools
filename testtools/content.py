# Copyright (c) 2009-2012 testtools developers. See LICENSE for details.

"""Content - a MIME-like Content object."""

__all__ = [
    'attach_file',
    'Content',
    'content_from_file',
    'content_from_stream',
    'text_content',
    'TracebackContent',
    ]

import codecs
import inspect
import json
import os
import sys
import traceback

from extras import try_import

from testtools.compat import _b, _format_exc_info, str_is_unicode, _u
from testtools.content_type import ContentType, JSON, UTF8_TEXT


functools = try_import('functools')

_join_b = _b("").join


DEFAULT_CHUNK_SIZE = 4096

STDOUT_LINE = '\nStdout:\n%s'
STDERR_LINE = '\nStderr:\n%s'


def _iter_chunks(stream, chunk_size, seek_offset=None, seek_whence=0):
    """Read 'stream' in chunks of 'chunk_size'.

    :param stream: A file-like object to read from.
    :param chunk_size: The size of each read from 'stream'.
    :param seek_offset: If non-None, seek before iterating.
    :param seek_whence: Pass through to the seek call, if seeking.
    """
    if seek_offset is not None:
        stream.seek(seek_offset, seek_whence)
    chunk = stream.read(chunk_size)
    while chunk:
        yield chunk
        chunk = stream.read(chunk_size)


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
            _join_b(self.iter_bytes()) == _join_b(other.iter_bytes()))

    def as_text(self):
        """Return all of the content as text.

        This is only valid where ``iter_text`` is.  It will load all of the
        content into memory.  Where this is a concern, use ``iter_text``
        instead.
        """
        return _u('').join(self.iter_text())

    def iter_bytes(self):
        """Iterate over bytestrings of the serialised content."""
        return self._get_bytes()

    def iter_text(self):
        """Iterate over the text of the serialised content.

        This is only valid for text MIME types, and will use ISO-8859-1 if
        no charset parameter is present in the MIME type. (This is somewhat
        arbitrary, but consistent with RFC2617 3.7.1).

        :raises ValueError: If the content type is not text/\*.
        """
        if self.content_type.type != "text":
            raise ValueError("Not a text type %r" % self.content_type)
        return self._iter_text()

    def _iter_text(self):
        """Worker for iter_text - does the decoding."""
        encoding = self.content_type.parameters.get('charset', 'ISO-8859-1')
        try:
            # 2.5+
            decoder = codecs.getincrementaldecoder(encoding)()
            for bytes in self.iter_bytes():
                yield decoder.decode(bytes)
            final = decoder.decode(_b(''), True)
            if final:
                yield final
        except AttributeError:
            # < 2.5
            bytes = ''.join(self.iter_bytes())
            yield bytes.decode(encoding)

    def __repr__(self):
        return "<Content type=%r, value=%r>" % (
            self.content_type, _join_b(self.iter_bytes()))


class StackTraceCommon(Content):

    def __init__(self, stack_trace_text):
        content_type = ContentType('text', 'x-traceback',
            {"language": "python", "charset": "utf8"})
        super(StackTraceCommon, self).__init__(
            content_type, lambda: [stack_trace_text.encode("utf8")])

    def _is_frame_in_unittest(self, frame):
        return '__unittest' in frame.f_globals


class TracebackContent(StackTraceCommon):
    """Content object for tracebacks.

    This adapts an exc_info tuple to the Content interface.
    text/x-traceback;language=python is used for the mime type, in order to
    provide room for other languages to format their tracebacks differently.
    """

    # Whether or not to hide layers of the stack trace that are
    # unittest/testtools internal code.  Defaults to True since the
    # system-under-test is rarely unittest or testtools.
    HIDE_INTERNAL_STACK = True

    def __init__(self, err, test):
        """Create a TracebackContent for err."""
        if err is None:
            raise ValueError("err may not be None")

        value = self._exc_info_to_unicode(err, test)
        super(TracebackContent, self).__init__(value)

    def _exc_info_to_unicode(self, err, test):
        """Converts a sys.exc_info()-style tuple of values into a string.

        Copied from Python 2.7's unittest.TestResult._exc_info_to_string.
        """
        exctype, value, tb = err
        # Skip test runner traceback levels
        if self.HIDE_INTERNAL_STACK:
            while tb and self._is_relevant_tb_level(tb):
                tb = tb.tb_next

        # testtools customization. When str is unicode (e.g. IronPython,
        # Python 3), traceback.format_exception returns unicode. For Python 2,
        # it returns bytes. We need to guarantee unicode.
        if str_is_unicode:
            format_exception = traceback.format_exception
        else:
            format_exception = _format_exc_info

        msgLines = format_exception(exctype, value, tb)

        if getattr(self, 'buffer', None):
            output = sys.stdout.getvalue()
            error = sys.stderr.getvalue()
            if output:
                if not output.endswith('\n'):
                    output += '\n'
                msgLines.append(STDOUT_LINE % output)
            if error:
                if not error.endswith('\n'):
                    error += '\n'
                msgLines.append(STDERR_LINE % error)
        return ''.join(msgLines)

    def _is_relevant_tb_level(self, tb):
        return self._is_frame_in_unittest(tb.tb_frame)


class StackTraceContent(StackTraceCommon):

    """Content object for displaying the current stack trace.

    This content object is useful for debugging - any time you wish to add the
    current python stack, simply create an instance of StackTraceContent and
    add it as a detail to the test.

    You may also pass in an additional string, which will be appended to the
    stack trace.

    text/x-traceback;language=python is used for the mime type, in order to
    provide room for other languages to format their tracebacks differently.
    """

    def __init__(self, additional_text='', skip=0):
        """Create a stack trace content object.

        :param skip: The number of stack frames to skip from the top of the
            stack.
        :param additional_text: Some text to append to the stack trace.
        :raises TypeError: if additional_text or skip are the incorrect type.
        """
        stack_lines = self._get_stack_lines(skip)
        if additional_text:
            stack_lines.append(additional_text)
        stack = "".join(stack_lines)

        content_type = ContentType('text', 'x-traceback',
            {"language": "python", "charset": "utf8"})
        super(StackTraceContent, self).__init__(stack)

    def _get_stack_lines(self, skip):
        top_frame = inspect.currentframe()
        for i in range(skip + 2):
            top_frame = top_frame.f_back
        # skip any frames that are in the testing framework itself:
        while top_frame and self._is_frame_in_unittest(top_frame):
            top_frame = top_frame.f_back

        limit = 0
        f = top_frame
        while f and not self._is_frame_in_unittest(f):
            limit += 1
            f = f.f_back

        return traceback.format_stack(top_frame, limit)


def json_content(json_data):
    """Create a JSON `Content` object from JSON-encodeable data."""
    data = json.dumps(json_data)
    if str_is_unicode:
        # The json module perversely returns native str not bytes
        data = data.encode('utf8')
    return Content(JSON, lambda: [data])


def text_content(text):
    """Create a `Content` object from some text.

    This is useful for adding details which are short strings.
    """
    return Content(UTF8_TEXT, lambda: [text.encode('utf8')])


def maybe_wrap(wrapper, func):
    """Merge metadata for func into wrapper if functools is present."""
    if functools is not None:
        wrapper = functools.update_wrapper(wrapper, func)
    return wrapper


def content_from_file(path, content_type=None, chunk_size=DEFAULT_CHUNK_SIZE,
                      buffer_now=False, seek_offset=None, seek_whence=0):
    """Create a `Content` object from a file on disk.

    Note that unless 'read_now' is explicitly passed in as True, the file
    will only be read from when ``iter_bytes`` is called.

    :param path: The path to the file to be used as content.
    :param content_type: The type of content.  If not specified, defaults
        to UTF8-encoded text/plain.
    :param chunk_size: The size of chunks to read from the file.
        Defaults to ``DEFAULT_CHUNK_SIZE``.
    :param buffer_now: If True, read the file from disk now and keep it in
        memory. Otherwise, only read when the content is serialized.
    :param seek_offset: If non-None, seek within the stream before reading it.
    :param seek_whence: If supplied, pass to stream.seek() when seeking.
    """
    if content_type is None:
        content_type = UTF8_TEXT
    def reader():
        # This should be try:finally:, but python2.4 makes that hard. When
        # We drop older python support we can make this use a context manager
        # for maximum simplicity.
        stream = open(path, 'rb')
        for chunk in _iter_chunks(stream, chunk_size, seek_offset, seek_whence):
            yield chunk
        stream.close()
    return content_from_reader(reader, content_type, buffer_now)


def content_from_stream(stream, content_type=None,
                        chunk_size=DEFAULT_CHUNK_SIZE, buffer_now=False,
                        seek_offset=None, seek_whence=0):
    """Create a `Content` object from a file-like stream.

    Note that the stream will only be read from when ``iter_bytes`` is
    called.

    :param stream: A file-like object to read the content from. The stream
        is not closed by this function or the content object it returns.
    :param content_type: The type of content. If not specified, defaults
        to UTF8-encoded text/plain.
    :param chunk_size: The size of chunks to read from the file.
        Defaults to ``DEFAULT_CHUNK_SIZE``.
    :param buffer_now: If True, reads from the stream right now. Otherwise,
        only reads when the content is serialized. Defaults to False.
    :param seek_offset: If non-None, seek within the stream before reading it.
    :param seek_whence: If supplied, pass to stream.seek() when seeking.
    """
    if content_type is None:
        content_type = UTF8_TEXT
    reader = lambda: _iter_chunks(stream, chunk_size, seek_offset, seek_whence)
    return content_from_reader(reader, content_type, buffer_now)


def content_from_reader(reader, content_type, buffer_now):
    """Create a Content object that will obtain the content from reader.

    :param reader: A callback to read the content. Should return an iterable of
        bytestrings.
    :param content_type: The content type to create.
    :param buffer_now: If True the reader is evaluated immediately and
        buffered.
    """
    if content_type is None:
        content_type = UTF8_TEXT
    if buffer_now:
        contents = list(reader())
        reader = lambda: contents
    return Content(content_type, reader)


def attach_file(detailed, path, name=None, content_type=None,
                chunk_size=DEFAULT_CHUNK_SIZE, buffer_now=True):
    """Attach a file to this test as a detail.

    This is a convenience method wrapping around ``addDetail``.

    Note that unless 'read_now' is explicitly passed in as True, the file
    *must* exist when the test result is called with the results of this
    test, after the test has been torn down.

    :param detailed: An object with details
    :param path: The path to the file to attach.
    :param name: The name to give to the detail for the attached file.
    :param content_type: The content type of the file.  If not provided,
        defaults to UTF8-encoded text/plain.
    :param chunk_size: The size of chunks to read from the file.  Defaults
        to something sensible.
    :param buffer_now: If False the file content is read when the content
        object is evaluated rather than when attach_file is called.
        Note that this may be after any cleanups that obj_with_details has, so
        if the file is a temporary file disabling buffer_now may cause the file
        to be read after it is deleted. To handle those cases, using
        attach_file as a cleanup is recommended because it guarantees a
        sequence for when the attach_file call is made::

            detailed.addCleanup(attach_file, 'foo.txt', detailed)
    """
    if name is None:
        name = os.path.basename(path)
    content_object = content_from_file(
        path, content_type, chunk_size, buffer_now)
    detailed.addDetail(name, content_object)
