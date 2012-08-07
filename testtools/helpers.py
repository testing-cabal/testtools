# Copyright (c) 2010-2011 testtools developers. See LICENSE for details.

__all__ = [
    'safe_hasattr',
    'try_import',
    'try_imports',
    ]

import sys


def try_import(name, alternative=None, error_callback=None):
    """Attempt to import ``name``.  If it fails, return ``alternative``.

    When supporting multiple versions of Python or optional dependencies, it
    is useful to be able to try to import a module.

    :param name: The name of the object to import, e.g. ``os.path`` or
        ``os.path.join``.
    :param alternative: The value to return if no module can be imported.
        Defaults to None.
    :param error_callback: If non-None, a callable that is passed the ImportError
        when the module cannot be loaded.
    """
    module_segments = name.split('.')
    last_error = None
    while module_segments:
        module_name = '.'.join(module_segments)
        try:
            module = __import__(module_name)
        except ImportError:
            last_error = sys.exc_info()[1]
            module_segments.pop()
            continue
        else:
            break
    else:
        if last_error is not None and error_callback is not None:
            error_callback(last_error)
        return alternative
    nonexistent = object()
    for segment in name.split('.')[1:]:
        module = getattr(module, segment, nonexistent)
        if module is nonexistent:
            if last_error is not None and error_callback is not None:
                error_callback(last_error)
            return alternative
    return module


_RAISE_EXCEPTION = object()
def try_imports(module_names, alternative=_RAISE_EXCEPTION, error_callback=None):
    """Attempt to import modules.

    Tries to import the first module in ``module_names``.  If it can be
    imported, we return it.  If not, we go on to the second module and try
    that.  The process continues until we run out of modules to try.  If none
    of the modules can be imported, either raise an exception or return the
    provided ``alternative`` value.

    :param module_names: A sequence of module names to try to import.
    :param alternative: The value to return if no module can be imported.
        If unspecified, we raise an ImportError.
    :param error_callback: If None, called with the ImportError for *each*
        module that fails to load.
    :raises ImportError: If none of the modules can be imported and no
        alternative value was specified.
    """
    module_names = list(module_names)
    for module_name in module_names:
        module = try_import(module_name, error_callback=error_callback)
        if module:
            return module
    if alternative is _RAISE_EXCEPTION:
        raise ImportError(
            "Could not import any of: %s" % ', '.join(module_names))
    return alternative


def safe_hasattr(obj, attr, _marker=object()):
    """Does 'obj' have an attribute 'attr'?

    Use this rather than built-in hasattr, as the built-in swallows exceptions
    in some versions of Python and behaves unpredictably with respect to
    properties.
    """
    return getattr(obj, attr, _marker) is not _marker


def _intersect_sets(a, b):
    """Return things in a only, things in both, things in b only."""
    return a - b, a & b, b - a


def _intersect_dicts(a, b):
    """Return three dicts, each representing one area of a Venn diagram.

    That is, return a dict of things that have keys in a but not b, a dict of
    things that have keys in both mapping to a tuple of a's value and b's
    value, and a dict of things in b but not in a.
    """
    a_only, common, b_only = _intersect_sets(set(a.keys()), set(b.keys()))
    return (
        dict((k, a[k]) for k in a_only),
        dict((k, (a[k], b[k])) for k in common),
        dict((k, b[k]) for k in b_only),
        )


def map_values(function, dictionary):
    """Map ``function`` across the values of ``dictionary``.

    :return: A dict with the same keys as ``dictionary``, where the value
        of each key ``k`` is ``function(dictionary[k])``.
    """
    return dict((k, function(dictionary[k])) for k in dictionary)


def filter_values(function, dictionary):
    """Filter ``dictionary`` by its values using ``function``."""
    return dict((k, v) for k, v in dictionary.items() if function(v))
