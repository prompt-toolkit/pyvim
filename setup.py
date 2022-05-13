#!/usr/bin/env python
import os
from setuptools import setup, find_packages
import pyvim

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
    long_description = f.read()


setup(
    name='pyvim',
    author='Jonathan Slenders',
    version=pyvim.__version__,
    license='BSD License',
    url='https://github.com/jonathanslenders/pyvim',
    description='Pure Python Vi Implementation',
    long_description=long_description,
    packages=find_packages('.'),
    install_requires = [
        'prompt_toolkit>=2.0.0,<3.1.0',
        'six',
        'pyflakes',        # For Python error reporting.
        'pygments',        # For the syntax highlighting.
        'docopt',          # For command line arguments.
    ],
    entry_points={
        'console_scripts': [
            'pyvim = pyvim.entry_points.run_pyvim:run',
        ]
    },
)
