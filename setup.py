#!/usr/bin/env python
import setuptools

try:
    import testtools
    cmd_class = {}
    if getattr(testtools, 'TestCommand', None) is not None:
        cmd_class['test'] = testtools.TestCommand
except:
    cmd_class = None


setuptools.setup(
    python_requires='>=3.5',
    cmdclass=cmd_class,
    setup_requires=['pbr'],
    pbr=True)
