# Copyright (c) 2010 Jonathan M. Lange. See LICENSE for details.

__all__ = [
    'try_import',
    'try_imports',
    ]


def try_import(module_name, alternative=None):
    """Attempt to import `module_name`.  If it fails, return `alternative`.

    When supporting multiple versions of Python or optional dependencies, it
    is useful to be able to try to import a module.

    :param module_name: The name of the module to import, e.g. 'os.path'.
    :param alternative: The value to return if no module can be imported.
        Defaults to None.
    """
    try:
        module = __import__(module_name)
    except ImportError:
        return alternative
    segments = module_name.split('.')[1:]
    for segment in segments:
        module = getattr(module, segment)
    return module


_RAISE_EXCEPTION = object()
def try_imports(module_names, alternative=_RAISE_EXCEPTION):
    """Attempt to import modules.

    Tries to import the first module in `module_names`.  If it can be
    imported, we return it.  If not, we go on to the second module and try
    that.  The process continues until we run out of modules to try.  If none
    of the modules can be imported, either raise an exception or return the
    provided `alternative` value.

    :param module_names: A sequence of module names to try to import.
    :param alternative: The value to return if no module can be imported.
        If unspecified, we raise an ImportError.
    :raises ImportError: If none of the modules can be imported and no
        alternative value was specified.
    """
    module_names = list(module_names)
    for module_name in module_names:
        module = try_import(module_name)
        if module:
            return module
    if alternative is _RAISE_EXCEPTION:
        raise ImportError(
            "Could not import any of: %s" % ', '.join(module_names))
    return alternative
