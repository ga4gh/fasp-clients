#!/usr/bin/env python

from setuptools import setup

setup(name='fasp-clients',
      version='1.2',
      packages=['fasp',
                'fasp.runner',
                'fasp.search',
                'fasp.loc',
                'fasp.workflow',
                'fasp.duri'],
      package_dir={'fasp': 'src/fasp'},
      include_package_data=True,
      install_requires=['requests',
					'pandas']
      )