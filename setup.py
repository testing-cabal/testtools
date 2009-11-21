#!/usr/bin/env python
"""Distutils installer for testtools."""

from distutils.core import setup

setup(name='testtools',
      author='Jonathan M. Lange',
      author_email='jml+testtools@mumak.net',
      url='https://launchpad.net/testtools',
      description=('Extensions to the Python standard library unit testing '
                   'framework'),
      version='0.9.0',
      packages=['testtools'])
