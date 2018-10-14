[![Unix Build Status][travis-image]][travis-link]
[![Requirements Status][requires-image]][requires-link]
[![pypi-version][pypi-image]][pypi-link]
![License][license-image-mit]

# PySpelling

## Overview

PySpelling is a module to help with automating spell checking with [Aspell](http://aspell.net/). It is essentially a wrapper around the Aspell command line utility, and allows you to setup different spelling tasks for different file types and filter the content as needed. It also allows you to do more advancing filtering of text via plugins since Aspell's filters are limited to a handful of types with limited options.

PySpelling is not designed to auto replace misspelled words or have interactive replace sessions, there are already modules to do that. PySpelling is mainly meant for automate reporting of spelling issues in different file types. So if you are looking for a find and replace spelling tool, this isn't for you.

## Documentation

Extension documentation is found here: http://facelessuser.github.io/pyspelling/.

## License

Rummage is released under the MIT license.

Copyright (c) 2017 - 2018 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

[travis-image]: https://img.shields.io/travis/facelessuser/pyspelling/master.svg?label=Unix%20Build
[travis-link]: https://travis-ci.org/facelessuser/pyspelling
[requires-image]: https://img.shields.io/requires/github/facelessuser/pyspelling/master.svg
[requires-link]: https://requires.io/github/facelessuser/pyspelling/requirements/?branch=master
[pypi-image]: https://img.shields.io/pypi/v/pyspelling.svg
[pypi-link]: https://pypi.python.org/pypi/pyspelling
[license-image-mit]: https://img.shields.io/badge/license-MIT-blue.svg
