#!/usr/bin/env python

from setuptools import setup

setup(name='fasp-clients',
      version='1.1',
      packages=['fasp',
                'fasp.runner',
                'fasp.search',
                'fasp.loc',
                'fasp.workflow'],
      package_dir={'fasp': 'src/fasp'},
      include_package_data=True,
      install_requires=['requests',
					'pandas']
      )