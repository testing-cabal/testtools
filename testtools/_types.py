# Copyright (c) 2026 testtools developers. See LICENSE for details.

from types import TracebackType
from typing import TypeAlias

# Type for exc_info tuples from sys.exc_info()
ExcInfo: TypeAlias = tuple[type[BaseException], BaseException, TracebackType | None]
OptExcInfo: TypeAlias = ExcInfo | tuple[None, None, None]
