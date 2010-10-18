#!/usr/bin/env python
"""Distutils installer for testtools."""

from distutils.core import setup
import os

import testtools


def get_revno():
    import bzrlib.workingtree
    t = bzrlib.workingtree.WorkingTree.open_containing(__file__)[0]
    return t.branch.revno()


def get_version():
    version = '.'.join(
        str(component) for component in testtools.__version__[0:3])
    phase = testtools.__version__[3]
    if phase == 'final':
        return version
    revno = get_revno()
    if phase == 'alpha':
        # No idea what the next version will be
        return 'next-%s' % revno
    else:
        # Preserve the version number but give it a revno prefix
        return version + '~%s' % revno


def get_long_description():
    manual_path = os.path.join(os.path.dirname(__file__), 'MANUAL')
    return open(manual_path).read()


setup(name='testtools',
      author='Jonathan M. Lange',
      author_email='jml+testtools@mumak.net',
      url='https://launchpad.net/testtools',
      description=('Extensions to the Python standard library unit testing '
                   'framework'),
      long_description=get_long_description(),
      version=get_version(),
      classifiers=["License :: OSI Approved :: MIT License"],
      packages=['testtools', 'testtools.testresult', 'testtools.tests'])
