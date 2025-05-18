[![Donate via PayPal][donate-image]][donate-link]
[![Build][github-ci-image]][github-ci-link]
[![Coverage Status][codecov-image]][codecov-link]
[![PyPI Version][pypi-image]][pypi-link]
[![PyPI - Python Version][python-image]][pypi-link]
[![License][license-image-mit]][license-link]
# PySpelling

## Overview

PySpelling is a module to help with automating spell checking in a project with [Aspell][aspell] or
[Hunspell][hunspell]. It is essentially a wrapper around the command line utility of these two spell checking tools, and
allows you to setup different spelling tasks for different file types. You can apply specific and different filters and
options to each task. PySpelling can also be used in CI environments to fail the build if there are misspelled words.

Aspell and Hunspell are very good spell checking tools. Aspell particularly comes with a couple of filters, but the
filters are limited in types and aren't extremely flexible. PySpelling was created to work around Aspell's and
Hunspell's filtering shortcomings by creating a wrapper around them that could be extended to handle more kinds of file
formats and provide more advanced filtering. If you need to filter out specific HTML tags with specific IDs or class
names, PySpelling can do it. If you want to scan Python files for docstrings, but also avoid specific content within the
docstring, you can do that as well. If PySpelling doesn't have a filter you need, with access to so many available
Python modules, you can easily write your own.

## Documentation

Extension documentation is found here: https://facelessuser.github.io/pyspelling/.

## License

MIT

[aspell]: http://aspell.net/
[hunspell]: https://hunspell.github.io/

[github-ci-image]: https://github.com/facelessuser/pyspelling/workflows/build/badge.svg
[github-ci-link]: https://github.com/facelessuser/pyspelling/actions?query=workflow%3Abuild+branch%3Amaster
[codecov-image]: https://img.shields.io/codecov/c/github/facelessuser/pyspelling/master.svg?logo=codecov&logoColor=aaaaaa&labelColor=333333
[codecov-link]: https://codecov.io/github/facelessuser/pyspelling
[pypi-image]: https://img.shields.io/pypi/v/pyspelling.svg?logo=pypi&logoColor=aaaaaa&labelColor=333333
[pypi-link]: https://pypi.python.org/pypi/pyspelling
[python-image]: https://img.shields.io/pypi/pyversions/pyspelling?logo=python&logoColor=aaaaaa&labelColor=333333
[license-image-mit]: https://img.shields.io/badge/license-MIT-blue.svg?labelColor=333333
[donate-image]: https://img.shields.io/badge/Donate-PayPal-3fabd1?logo=paypal
[donate-link]: https://www.paypal.me/facelessuser
