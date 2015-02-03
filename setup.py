from setuptools import setup, find_packages

try:
    long_description = open("README.rst").read()
except IOError:
    long_description = ""

setup(
    name="ptvim",
    version="0.1.0",
    description="Pure python vim clone",
    license="MIT",
    author="Jonathan Slenders",
    url="https://github.com/jonathanslenders/ptvim",
    packages=find_packages(),
    install_requires=["prompt_toolkit", "docopt"],
    long_description=long_description,
    entry_points={
        'console_scripts': [
            'ptvim=ptvim:run',
        ],
    },
)
