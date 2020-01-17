[![Gitter][gitter-image]][gitter-link]
[![Build][github-ci-image]][github-ci-link]
[![Unix Build Status][travis-image]][travis-link]
[![Windows Build Status][appveyor-image]][appveyor-link]
[![Coverage Status][codecov-image]][codecov-link]
[![PyPI Version][pypi-image]][pypi-link]
[![PyPI - Python Version][python-image]][pypi-link]
![License][license-image-mit]
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

PySpelling is released under the MIT license.

Copyright (c) 2017 - 2020 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

[aspell]: http://aspell.net/
[hunspell]: https://hunspell.github.io/

[gitter-image]: https://img.shields.io/gitter/room/facelessuser/pyspelling.svg?logo=gitter&color=fuchsia&logoColor=cccccc
[gitter-link]: https://gitter.im/facelessuser/pyspelling
[github-ci-image]: https://github.com/facelessuser/pyspelling/workflows/build/badge.svg
[github-ci-link]: https://github.com/facelessuser/pyspelling/actions?workflow=build
[codecov-image]: https://img.shields.io/codecov/c/github/facelessuser/pyspelling/master.svg?logo=codecov&logoColor=cccccc
[codecov-link]: https://codecov.io/github/facelessuser/pyspelling
[appveyor-image]: https://img.shields.io/appveyor/ci/facelessuser/pyspelling/master.svg?label=appveyor&logo=appveyor&logoColor=cccccc
[appveyor-link]: https://ci.appveyor.com/project/facelessuser/pyspelling
[travis-image]: https://img.shields.io/travis/facelessuser/pyspelling/master.svg?label=travis&logo=travis%20ci&logoColor=cccccc
[travis-link]: https://travis-ci.org/facelessuser/pyspelling
[pypi-image]: https://img.shields.io/pypi/v/pyspelling.svg?logo=pypi&logoColor=cccccc
[pypi-link]: https://pypi.python.org/pypi/pyspelling
[python-image]: https://img.shields.io/pypi/pyversions/pyspelling?logo=python&logoColor=cccccc
[license-image-mit]: https://img.shields.io/badge/license-MIT-blue.svg
