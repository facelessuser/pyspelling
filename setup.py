#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup pymdown-extensions."""

from setuptools import setup, find_packages
import os
import imp
import sys


def get_version():
    """Get version and version_info without importing the entire module."""

    path = os.path.join(os.path.dirname(__file__), 'pyspelling')
    fp, pathname, desc = imp.find_module('__meta__', [path])
    try:
        meta = imp.load_module('__meta__', fp, pathname, desc)
        return meta.__version__, meta.__version_info__._get_dev_status()
    finally:
        fp.close()


def get_requirements():
    """Get the dependencies."""

    with open("requirements/project.txt") as f:
        requirements = []
        for line in f.readlines():
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
    return requirements


def get_description():
    """Get long description."""

    with open("README.md", 'r') as f:
        desc = f.read()
    return desc


VER, DEVSTATUS = get_version()

entry_points = {
    'console_scripts': [
        'pyspelling=pyspelling.__main__:main',
        'pyspelling%d.%d=pyspelling.__main__:main' % sys.version_info[:2]
    ]
}

setup(
    name='pyspelling',
    version=VER,
    keywords='spelling',
    description='Spell checker.',
    long_description=get_description(),
    long_description_content_type='text/markdown',
    author='Isaac Muse',
    author_email='Isaac.Muse@gmail.com',
    url='https://github.com/facelessuser/pyspelling',
    packages=find_packages(exclude=['tests', 'tools']),
    entry_points=entry_points,
    install_requires=get_requirements(),
    license='MIT License',
    classifiers=[
        'Development Status :: %s' % DEVSTATUS,
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
