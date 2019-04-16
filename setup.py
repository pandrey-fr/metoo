# coding: utf-8

"""Setup for the installation of the 'metoo' package.

NOTE: as this package provides database-specific tools,
      its installation is not mandatory for usage, and
      should preferably be done in a virtual environment
      dedicated to studying said database.
"""

import setuptools
from setuptools.command.install import install

setuptools.setup(
    name='metoo',
    version='0.1',
    packages=setuptools.find_packages(),
    include_package_data=True,
    author='Paul Andrey',
    description='database-specific tools to analyze #MeToo spread on Twitter',
    license='GPLv3',
    install_requires=[
        'matplotlib >= 3.0'
        'networkx >= 2.0',
        'numpy >= 1.12',
        'pandas >= 0.20'
    ],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6"
    ]
)
