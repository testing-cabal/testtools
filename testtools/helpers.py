# Copyright (c) 2010-2012 testtools developers. See LICENSE for details.

from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
R = TypeVar("R")


def map_values(function: Callable[[V], R], dictionary: dict[K, V]) -> dict[K, R]:
    """Map ``function`` across the values of ``dictionary``.

    :return: A dict with the same keys as ``dictionary``, where the value
        of each key ``k`` is ``function(dictionary[k])``.
    """
    return {k: function(dictionary[k]) for k in dictionary}


def filter_values(function: Callable[[V], bool], dictionary: dict[K, V]) -> dict[K, V]:
    """Filter ``dictionary`` by its values using ``function``."""
    return {k: v for k, v in dictionary.items() if function(v)}


def dict_subtract(a: dict[K, V], b: dict[K, Any]) -> dict[K, V]:
    """Return the part of ``a`` that's not in ``b``."""
    return {k: a[k] for k in set(a) - set(b)}


def list_subtract(a: list[T], b: list[T]) -> list[T]:
    """Return a list ``a`` without the elements of ``b``.

    If a particular value is in ``a`` twice and ``b`` once then the returned
    list then that value will appear once in the returned list.
    """
    a_only = list(a)
    for x in b:
        if x in a_only:
            a_only.remove(x)
    return a_only
