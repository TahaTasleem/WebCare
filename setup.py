"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='webdirect',
    version='1.6.0',

    # WebDirect Details
    description='WebDirect',
    long_description=long_description,
    url='https://www.campana.com',
    author='Campana Systems Inc.',
    author_email='atdev@campana.com',

    # add support for git repository
    # use_scm_version=True,
    setup_requires=['setuptools_scm'],

    classifiers=[
        'Development Status :: 5 - Stable',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.9'
    ],

    # Add required packages
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    py_modules=["webdirect", "webrouting"],
    include_package_data=True,

    # Dependencies
    install_requires=['click>=7.1',
                      'Flask>=1.1',
                      'waitress>=1.4',
                      'csipyutils>=1.1',
                      'paramiko>=2.7'],

    # Main Entry Point
    entry_points={
        'console_scripts': [
            'webdirect=webdirect:main',
        ],
    },
)
