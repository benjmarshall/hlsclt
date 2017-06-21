"""A setuptools based setup module.
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Get the version number
version = {}
with open("hlsclt/_version.py") as fp:
    exec(fp.read(), version)

setup(
    name='hlsclt',

    version=version['__version__'],

    description='A Vivado HLS Command Line Helper Tool',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/benjmarshall/hlsclt',

    # Author details
    author='Ben Marshall',
    author_email='sayhello@benmarshall.co.uk',

    # Choose your license
    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6'
    ],

    keywords='xilinx vivado development',

    packages=find_packages(),

    install_requires=['Click'],

    entry_points = {
        'console_scripts': ['hlsclt=hlsclt.hlsclt:cli']
    },

    include_package_data=True,

)
