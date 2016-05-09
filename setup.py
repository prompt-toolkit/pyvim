#!/usr/bin/env python
import os
from setuptools import setup, find_packages
import pyvim

long_description = open(
    os.path.join(
        os.path.dirname(__file__),
        'README.rst'
    )
).read()


setup(
    name='pyvim',
    author='Jonathan Slenders',
    version=pyvim.__version__,
    license='LICENSE',
    url='https://github.com/jonathanslenders/pyvim',
    description='Pure Python Vi Implementation',
    long_description=long_description,
    packages=find_packages('.'),
    install_requires = [
        'prompt_toolkit>=1.0.0,<1.1.0',
        'ptpython==0.34',  # For the Python completion (with Jedi.)
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
