#!/usr/bin/env python3

import os
from distutils.core import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='targomiko',
      version='0.1.0',
      description='Wrapper for paramiko, focused on easy remote command handling of IO, waiting, abortion and exit-code retrieval.',
      long_description=read('README.md'),
      author='Luca Corbatto',
      author_email='luca@corbatto.de',
      packages=['targomiko'],
      )
