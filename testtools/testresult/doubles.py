# Copyright (c) 2009-2016 testtools developers. See LICENSE for details.

"""Doubles of test result objects, useful for testing unittest code."""

import datetime
import unittest
from collections import namedtuple
from collections.abc import Iterable
from typing import Literal, TypeAlias

from testtools.tags import TagContext

__all__ = [
    "ExtendedTestResult",
    "Python3TestResult",
    "StreamResult",
    "TwistedTestResult",
]

# Convenience namedtuple for status events - defined early for use in LogEvent
_StatusEvent = namedtuple(
    "_StatusEvent",
    [
        "name",
        "test_id",
        "test_status",
        "test_tags",
        "runnable",
        "file_name",
        "file_bytes",
        "eof",
        "mime_type",
        "route_code",
        "timestamp",
    ],
)

# Event type aliases using plain tuples with Literal for event names
# This provides type safety while working with the existing plain tuple code
LogEvent: TypeAlias = (
    tuple[Literal["startTestRun"]]
    | tuple[Literal["stopTestRun"]]
    | tuple[Literal["startTest"], unittest.TestCase]
    | tuple[Literal["stopTest"], unittest.TestCase]
    | tuple[Literal["addSuccess"], unittest.TestCase]
    | tuple[Literal["addSuccess"], unittest.TestCase, dict[str, object]]
    | tuple[
        Literal["addError"],
        unittest.TestCase,
        tuple[type, Exception, object] | dict[str, object] | None | object,
    ]
    | tuple[
        Literal["addFailure"],
        unittest.TestCase,
        tuple[type, Exception, object] | dict[str, object] | None | object,
    ]
    | tuple[
        Literal["addExpectedFailure"],
        unittest.TestCase,
        tuple[type, Exception, object] | dict[str, object] | None | object,
    ]
    | tuple[
        Literal["addSkip"],
        unittest.TestCase,
        str | dict[str, object] | None,
    ]
    | tuple[Literal["addUnexpectedSuccess"], unittest.TestCase]
    | tuple[Literal["addUnexpectedSuccess"], unittest.TestCase, dict[str, object]]
    | tuple[Literal["addDuration"], unittest.TestCase, float]
    | tuple[Literal["progress"], int, int]
    | tuple[Literal["tags"], Iterable[str], Iterable[str]]
    | tuple[Literal["time"], datetime.datetime]
    | _StatusEvent
)


class LoggingBase:
    """Basic support for logging of results."""

    def __init__(self, event_log: list[LogEvent] | None = None) -> None:
        if event_log is None:
            event_log = []
        self._events = event_log


class Python3TestResult(LoggingBase):
    """A precisely python 3 like test result, that logs."""

    def __init__(self, event_log: list[LogEvent] | None = None) -> None:
        super().__init__(event_log=event_log)
        self.shouldStop = False
        self._was_successful = True
        self.testsRun = 0
        self.failfast = False
        self.collectedDurations: list[tuple[unittest.TestCase, float]] = []

    def addError(
        self, test: unittest.TestCase, err: tuple[type, Exception, object]
    ) -> None:
        self._was_successful = False
        self._events.append(("addError", test, err))
        if self.failfast:
            self.stop()

    def addFailure(
        self, test: unittest.TestCase, err: tuple[type, Exception, object]
    ) -> None:
        self._was_successful = False
        self._events.append(("addFailure", test, err))
        if self.failfast:
            self.stop()

    def addSuccess(self, test: unittest.TestCase) -> None:
        self._events.append(("addSuccess", test))

    def addExpectedFailure(
        self, test: unittest.TestCase, err: tuple[type, Exception, object]
    ) -> None:
        self._events.append(("addExpectedFailure", test, err))

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:
        self._events.append(("addSkip", test, reason))

    def addUnexpectedSuccess(self, test: unittest.TestCase) -> None:
        self._events.append(("addUnexpectedSuccess", test))
        if self.failfast:
            self.stop()

    def addDuration(self, test: unittest.TestCase, duration: float) -> None:
        self._events.append(("addDuration", test, duration))
        self.collectedDurations.append((test, duration))

    def startTest(self, test: unittest.TestCase) -> None:
        self._events.append(("startTest", test))
        self.testsRun += 1

    def startTestRun(self) -> None:
        self._events.append(("startTestRun",))

    def stop(self) -> None:
        self.shouldStop = True

    def stopTest(self, test: unittest.TestCase) -> None:
        self._events.append(("stopTest", test))

    def stopTestRun(self) -> None:
        self._events.append(("stopTestRun",))

    def wasSuccessful(self) -> bool:
        return self._was_successful


class ExtendedTestResult(Python3TestResult):
    """A test result like the proposed extended unittest result API."""

    def __init__(self, event_log: list[LogEvent] | None = None) -> None:
        super().__init__(event_log)
        self._tags = TagContext()

    def addError(
        self,
        test: unittest.TestCase,
        err: tuple[type, Exception, object] | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        self._was_successful = False
        self._events.append(("addError", test, err or details))

    def addFailure(
        self,
        test: unittest.TestCase,
        err: tuple[type, Exception, object] | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        self._was_successful = False
        self._events.append(("addFailure", test, err or details))

    def addExpectedFailure(
        self,
        test: unittest.TestCase,
        err: tuple[type, Exception, object] | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        self._events.append(("addExpectedFailure", test, err or details))

    def addSkip(
        self,
        test: unittest.TestCase,
        reason: str | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        self._events.append(("addSkip", test, reason or details))

    def addSuccess(
        self, test: unittest.TestCase, details: dict[str, object] | None = None
    ) -> None:
        if details:
            self._events.append(("addSuccess", test, details))
        else:
            self._events.append(("addSuccess", test))

    def addUnexpectedSuccess(
        self, test: unittest.TestCase, details: dict[str, object] | None = None
    ) -> None:
        self._was_successful = False
        if details is not None:
            self._events.append(("addUnexpectedSuccess", test, details))
        else:
            self._events.append(("addUnexpectedSuccess", test))

    def addDuration(self, test: unittest.TestCase, duration: float) -> None:
        self._events.append(("addDuration", test, duration))

    def progress(self, offset: int, whence: int) -> None:
        self._events.append(("progress", offset, whence))

    def startTestRun(self) -> None:
        super().startTestRun()
        self._was_successful = True
        self._tags = TagContext()

    def startTest(self, test: unittest.TestCase) -> None:
        super().startTest(test)
        self._tags = TagContext(self._tags)

    def stopTest(self, test: unittest.TestCase) -> None:
        # NOTE: In Python 3.12.1 skipped tests may not call startTest()
        if self._tags is not None and self._tags.parent is not None:
            self._tags = self._tags.parent
        super().stopTest(test)

    @property
    def current_tags(self) -> set[str]:
        return self._tags.get_current_tags()

    def tags(self, new_tags: Iterable[str], gone_tags: Iterable[str]) -> None:
        self._tags.change_tags(new_tags, gone_tags)
        self._events.append(("tags", new_tags, gone_tags))

    def time(self, time: datetime.datetime) -> None:
        self._events.append(("time", time))

    def wasSuccessful(self) -> bool:
        return self._was_successful


class TwistedTestResult(LoggingBase):
    """Emulate the relevant bits of :py:class:`twisted.trial.itrial.IReporter`.

    Used to ensure that we can use ``trial`` as a test runner.
    """

    def __init__(self, event_log: list[LogEvent] | None = None) -> None:
        super().__init__(event_log=event_log)
        self._was_successful = True
        self.testsRun = 0

    def startTest(self, test: unittest.TestCase) -> None:
        self.testsRun += 1
        self._events.append(("startTest", test))

    def stopTest(self, test: unittest.TestCase) -> None:
        self._events.append(("stopTest", test))

    def addSuccess(self, test: unittest.TestCase) -> None:
        self._events.append(("addSuccess", test))

    def addError(self, test: unittest.TestCase, error: object) -> None:
        self._was_successful = False
        self._events.append(("addError", test, error))

    def addFailure(self, test: unittest.TestCase, error: object) -> None:
        self._was_successful = False
        self._events.append(("addFailure", test, error))

    def addExpectedFailure(
        self, test: unittest.TestCase, failure: object, todo: object | None = None
    ) -> None:
        self._events.append(("addExpectedFailure", test, failure))

    def addUnexpectedSuccess(
        self, test: unittest.TestCase, todo: object | None = None
    ) -> None:
        self._events.append(("addUnexpectedSuccess", test))

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:
        self._events.append(("addSkip", test, reason))

    def wasSuccessful(self) -> bool:
        return self._was_successful

    def done(self) -> None:
        pass


class StreamResult(LoggingBase):
    """A StreamResult implementation for testing.

    All events are logged to _events.
    """

    def startTestRun(self) -> None:
        self._events.append(("startTestRun",))

    def stopTestRun(self) -> None:
        self._events.append(("stopTestRun",))

    def status(
        self,
        test_id: str | None = None,
        test_status: str | None = None,
        test_tags: set[str] | None = None,
        runnable: bool = True,
        file_name: str | None = None,
        file_bytes: bytes | None = None,
        eof: bool = False,
        mime_type: str | None = None,
        route_code: str | None = None,
        timestamp: datetime.datetime | None = None,
    ) -> None:
        self._events.append(
            _StatusEvent(
                "status",
                test_id,
                test_status,
                test_tags,
                runnable,
                file_name,
                file_bytes,
                eof,
                mime_type,
                route_code,
                timestamp,
            )
        )
