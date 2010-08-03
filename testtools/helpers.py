# Copyright (c) 2010 Jonathan M. Lange. See LICENSE for details.


def try_import(module_name, alternative=None):
    try:
        return __import__(module_name)
    except ImportError:
        return alternative
