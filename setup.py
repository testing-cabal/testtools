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
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    cmdclass=cmd_class,
    setup_requires=['pbr'],
    pbr=True)
