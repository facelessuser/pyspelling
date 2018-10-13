#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup pymdown-extensions."""

from setuptools import setup, find_packages
import os
import imp

LONG_DESC = '''
PySpelling is a spell checker that wraps around Aspell.
You can check out the list of available extensions and learn more about them by `reading the docs`_.

.. _`reading the docs`: http://facelessuser.github.io/pyspelling/

Support
=======

Help and support is available here at the repositories `bug tracker`_.
Please read about `support and contributing`_ before creating issues.

.. _`bug tracker`: https://github.com/facelessuser/pyspelling/issues
.. _`support and contributing`: http://facelessuser.github.io/pyspelling/contributing/
'''


def get_version():
    """Get version and version_info without importing the entire module."""

    devstatus = {
        'alpha': '3 - Alpha',
        'beta': '4 - Beta',
        'candidate': '4 - Beta',
        'final': '5 - Production/Stable'
    }
    path = os.path.join(os.path.dirname(__file__), 'pyspelling')
    fp, pathname, desc = imp.find_module('__version__', [path])
    try:
        v = imp.load_module('__version__', fp, pathname, desc)
        return v.version, devstatus[v.version_info[3]]
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


VER, DEVSTATUS = get_version()

entry_points = {
    'console_scripts': [
        'pyspelling=pyspelling.__main__:main'
    ]
}

setup(
    name='pyspelling',
    version=VER,
    keywords='spelling',
    description='Spell checker.',
    long_description=LONG_DESC,
    author='Isaac Muse',
    author_email='Isaac.Muse@gmail.com',
    url='https://github.com/facelessuser/pyspelling',
    packages=find_packages(exclude=['tools', 'tests']),
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
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
