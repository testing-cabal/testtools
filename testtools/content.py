# Copyright (c) 2009-2012 testtools developers. See LICENSE for details.

"""Content - a MIME-like Content object."""

__all__ = [
    "Content",
    "TracebackContent",
    "attach_file",
    "content_from_file",
    "content_from_stream",
    "json_content",
    "text_content",
]

import codecs
import functools
import json
import os
import traceback
import types
from collections.abc import Callable, Iterable, Iterator
from typing import IO, Any, Protocol, TypeAlias, runtime_checkable

from testtools.content_type import JSON, UTF8_TEXT, ContentType

# Type for JSON-serializable data
JSONType: TypeAlias = (
    dict[str, "JSONType"] | list["JSONType"] | str | int | float | bool | None
)


class _Detailed(Protocol):
    """Protocol for objects that have an addDetail method."""

    def addDetail(self, name: str, content_object: "Content") -> None: ...


@runtime_checkable
class _TestCase(Protocol):
    """Protocol for test objects used in TracebackContent."""

    failureException: Any  # Can be type[BaseException], tuple, or None


DEFAULT_CHUNK_SIZE = 4096

STDOUT_LINE = "\nStdout:\n%s"
STDERR_LINE = "\nStderr:\n%s"


def _iter_chunks(
    stream: IO[bytes],
    chunk_size: int,
    seek_offset: int | None = None,
    seek_whence: int = 0,
) -> Iterator[bytes]:
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


class Content:
    """A MIME-like Content object.

    'Content' objects can be serialised to bytes using the iter_bytes method.
    If the 'Content-Type' is recognised by other code, they are welcome to
    look for richer contents that mere byte serialisation - for example in
    memory object graphs etc. However, such code MUST be prepared to receive
    a generic 'Content' object that has been reconstructed from a byte stream.

    :ivar content_type: The content type of this Content.
    """

    def __init__(
        self, content_type: ContentType, get_bytes: Callable[[], Iterable[bytes]]
    ) -> None:
        """Create a ContentType."""
        if None in (content_type, get_bytes):
            raise ValueError(f"None not permitted in {content_type!r}, {get_bytes!r}")
        self.content_type = content_type
        self._get_bytes = get_bytes

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Content):
            return NotImplemented
        return bool(
            self.content_type == other.content_type
            and b"".join(self.iter_bytes()) == b"".join(other.iter_bytes())
        )

    def as_text(self) -> str:
        """Return all of the content as text.

        This is only valid where ``iter_text`` is.  It will load all of the
        content into memory.  Where this is a concern, use ``iter_text``
        instead.
        """
        return "".join(self.iter_text())

    def iter_bytes(self) -> Iterator[bytes]:
        """Iterate over bytestrings of the serialised content."""
        return iter(self._get_bytes())

    def iter_text(self) -> Iterator[str]:
        """Iterate over the text of the serialised content.

        This is only valid for text MIME types, and will use ISO-8859-1 if
        no charset parameter is present in the MIME type. (This is somewhat
        arbitrary, but consistent with RFC2617 3.7.1).

        :raises ValueError: If the content type is not "text/*".
        """
        if self.content_type.type != "text":
            raise ValueError(f"Not a text type {self.content_type!r}")
        return self._iter_text()

    def _iter_text(self) -> Iterator[str]:
        """Worker for iter_text - does the decoding."""
        encoding = self.content_type.parameters.get("charset", "ISO-8859-1")
        decoder = codecs.getincrementaldecoder(encoding)()
        for bytes in self.iter_bytes():
            yield decoder.decode(bytes)
        final = decoder.decode(b"", True)
        if final:
            yield final

    def __repr__(self) -> str:
        return (
            f"<Content type={self.content_type!r}, "
            f"value={b''.join(self.iter_bytes())!r}>"
        )


class StackLinesContent(Content):
    """Content object for stack lines.

    This adapts a list of "preprocessed" stack lines into a 'Content' object.
    The stack lines are most likely produced from ``traceback.extract_stack``
    or ``traceback.extract_tb``.

    text/x-traceback;language=python is used for the mime type, in order to
    provide room for other languages to format their tracebacks differently.
    """

    # Whether or not to hide layers of the stack trace that are
    # unittest/testtools internal code.  Defaults to True since the
    # system-under-test is rarely unittest or testtools.
    HIDE_INTERNAL_STACK = True

    def __init__(
        self,
        stack_lines: traceback.StackSummary,
        prefix_content: str = "",
        postfix_content: str = "",
    ) -> None:
        """Create a StackLinesContent for ``stack_lines``.

        :param stack_lines: A list of preprocessed stack lines, probably
            obtained by calling ``traceback.extract_stack`` or
            ``traceback.extract_tb``.
        :param prefix_content: If specified, a unicode string to prepend to the
            text content.
        :param postfix_content: If specified, a unicode string to append to the
            text content.
        """
        content_type = ContentType(
            "text", "x-traceback", {"language": "python", "charset": "utf8"}
        )
        value = (
            prefix_content + self._stack_lines_to_unicode(stack_lines) + postfix_content
        )
        super().__init__(content_type, lambda: [value.encode("utf8")])

    def _stack_lines_to_unicode(self, stack_lines: traceback.StackSummary) -> str:
        """Converts a list of pre-processed stack lines into a unicode string."""
        msg_lines = traceback.format_list(stack_lines)
        return "".join(msg_lines)


class TracebackContent(Content):
    """Content object for tracebacks.

    This adapts an exc_info tuple to the 'Content' interface.
    'text/x-traceback;language=python' is used for the mime type, in order to
    provide room for other languages to format their tracebacks differently.
    """

    def __init__(
        self,
        err: tuple[type[BaseException], BaseException, types.TracebackType | None]
        | tuple[None, None, None],
        test: _TestCase | None,
        capture_locals: bool = False,
    ) -> None:
        """Create a TracebackContent for ``err``.

        :param err: An exc_info error tuple.
        :param test: A test object used to obtain failureException.
        :param capture_locals: If true, show locals in the traceback.
        """
        if err is None:
            raise ValueError("err may not be None")

        exctype, value, tb = err
        # Ensure we have a real exception, not the (None, None, None) variant
        assert exctype is not None, "exctype must not be None"
        assert value is not None, "value must not be None"
        # Skip test runner traceback levels
        if StackLinesContent.HIDE_INTERNAL_STACK:
            while tb and "__unittest" in tb.tb_frame.f_globals:
                tb = tb.tb_next

        limit = None
        # Disabled due to https://bugs.launchpad.net/testtools/+bug/1188420
        if (
            False
            and StackLinesContent.HIDE_INTERNAL_STACK
            and test is not None
            and test.failureException
            and isinstance(value, test.failureException)
        ):
            # Skip assert*() traceback levels
            limit = 0
            while tb and not self._is_relevant_tb_level(tb):
                limit += 1
                tb = tb.tb_next

        stack_lines = list(
            traceback.TracebackException(
                exctype, value, tb, limit=limit, capture_locals=capture_locals
            ).format()
        )
        content_type = ContentType(
            "text", "x-traceback", {"language": "python", "charset": "utf8"}
        )
        super().__init__(content_type, lambda: [x.encode("utf8") for x in stack_lines])


def StacktraceContent(prefix_content: str = "", postfix_content: str = "") -> Content:
    """Content object for stack traces.

    This function will create and return a 'Content' object that contains a
    stack trace.

    The mime type is set to 'text/x-traceback;language=python', so other
    languages can format their stack traces differently.

    :param prefix_content: A unicode string to add before the stack lines.
    :param postfix_content: A unicode string to add after the stack lines.
    """
    stack = traceback.walk_stack(None)

    def filter_stack(
        stack: Iterator[tuple[types.FrameType, int]],
    ) -> Iterator[tuple[types.FrameType, int]]:
        # Discard the filter_stack frame.
        next(stack)
        # Discard the StacktraceContent frame.
        next(stack)
        for f, f_lineno in stack:
            if StackLinesContent.HIDE_INTERNAL_STACK:
                if "__unittest" in f.f_globals:
                    return
                yield f, f_lineno

    extract = traceback.StackSummary.extract(filter_stack(stack))
    extract.reverse()
    return StackLinesContent(extract, prefix_content, postfix_content)


def json_content(json_data: JSONType) -> Content:
    """Create a JSON Content object from JSON-encodeable data."""
    json_str = json.dumps(json_data)
    # The json module perversely returns native str not bytes
    data = json_str.encode("utf8")
    return Content(JSON, lambda: [data])


def text_content(text: str) -> Content:
    """Create a Content object from some text.

    This is useful for adding details which are short strings.
    """
    if not isinstance(text, str):
        raise TypeError(
            f"text_content must be given text, not '{type(text).__name__}'."
        )
    return Content(UTF8_TEXT, lambda: [text.encode("utf8")])


def maybe_wrap(
    wrapper: Callable[..., Any], func: Callable[..., Any]
) -> Callable[..., Any]:
    """Merge metadata for func into wrapper if functools is present."""
    if functools is not None:
        wrapper = functools.update_wrapper(wrapper, func)
    return wrapper


def content_from_file(
    path: str,
    content_type: ContentType | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    buffer_now: bool = False,
    seek_offset: int | None = None,
    seek_whence: int = 0,
) -> Content:
    """Create a Content object from a file on disk.

    Note that unless ``buffer_now`` is explicitly passed in as True, the file
    will only be read from when ``iter_bytes`` is called.

    :param path: The path to the file to be used as content.
    :param content_type: The type of content.  If not specified, defaults
        to UTF8-encoded text/plain.
    :param chunk_size: The size of chunks to read from the file.
        Defaults to ``DEFAULT_CHUNK_SIZE``.
    :param buffer_now: If True, read the file from disk now and keep it in
        memory. Otherwise, only read when the content is serialized.
    :param seek_offset: If non-None, seek within the stream before reading it.
    :param seek_whence: If supplied, pass to ``stream.seek()`` when seeking.
    """
    if content_type is None:
        content_type = UTF8_TEXT

    def reader() -> Iterable[bytes]:
        with open(path, "rb") as stream:
            yield from _iter_chunks(stream, chunk_size, seek_offset, seek_whence)

    return content_from_reader(reader, content_type, buffer_now)


def content_from_stream(
    stream: IO[bytes],
    content_type: ContentType | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    buffer_now: bool = False,
    seek_offset: int | None = None,
    seek_whence: int = 0,
) -> Content:
    """Create a Content object from a file-like stream.

    Note that unless ``buffer_now`` is explicitly passed in as True, the stream
    will only be read from when ``iter_bytes`` is called.

    :param stream: A file-like object to read the content from. The stream
        is not closed by this function or the 'Content' object it returns.
    :param content_type: The type of content. If not specified, defaults
        to UTF8-encoded text/plain.
    :param chunk_size: The size of chunks to read from the file.
        Defaults to ``DEFAULT_CHUNK_SIZE``.
    :param buffer_now: If True, reads from the stream right now. Otherwise,
        only reads when the content is serialized. Defaults to False.
    :param seek_offset: If non-None, seek within the stream before reading it.
    :param seek_whence: If supplied, pass to ``stream.seek()`` when seeking.
    """
    if content_type is None:
        content_type = UTF8_TEXT

    def reader() -> Iterator[bytes]:
        return _iter_chunks(stream, chunk_size, seek_offset, seek_whence)

    return content_from_reader(reader, content_type, buffer_now)


def content_from_reader(
    reader: Callable[[], Iterable[bytes]],
    content_type: ContentType | None,
    buffer_now: bool,
) -> Content:
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

        def buffered_reader() -> Iterable[bytes]:
            return contents

        return Content(content_type, buffered_reader)

    return Content(content_type, reader)


def attach_file(
    detailed: _Detailed,
    path: str,
    name: str | None = None,
    content_type: ContentType | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    buffer_now: bool = True,
) -> None:
    """Attach a file to this test as a detail.

    This is a convenience method wrapping around ``addDetail``.

    Note that by default the contents of the file will be read immediately. If
    ``buffer_now`` is False, then the file *must* exist when the test result is
    called with the results of this test, after the test has been torn down.

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
    content_object = content_from_file(path, content_type, chunk_size, buffer_now)
    detailed.addDetail(name, content_object)
