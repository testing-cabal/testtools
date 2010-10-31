# Copyright (c) 2010 Jonathan M. Lange. See LICENSE for details.


def try_import(module_name, alternative=None):
    """Attempt to import `module_name`.  If it fails, return `alternative`.

    When supporting multiple versions of Python or optional dependencies, it
    is useful to be able to try to import a module.
    """
    try:
        module = __import__(module_name)
    except ImportError:
        return alternative
    segments = module_name.split('.')[1:]
    for segment in segments:
        module = getattr(module, segment)
    return module
