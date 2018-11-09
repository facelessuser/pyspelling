# Basic Usage

## Overview

PySpelling is a module to help with automating spell checking in a project with [Aspell][aspell] or [Hunspell][hunspell]. It is essentially a wrapper around the command line utility of these two spell checking tools, and allows you to setup different spelling tasks for different file types. You can apply specific and different filters and options to each task. PySpelling can also be used in CI environments to fail the build if there are misspelled words.

Aspell and Hunspell are very good spell checking tools. Aspell particularly comes with a couple of filters, but the filters are limited in types and aren't extremely flexible. PySpelling was created to work around Aspell's and Hunspell's filtering shortcomings by creating a wrapper around them that could be extended to handle more kinds of file formats and provide more advanced filtering. If you need to filter out specific HTML tags with specific IDs or class names, PySpelling can do it. If you want to scan Python files for docstrings, but also avoid specific content within the docstring, you can do that as well. If PySpelling doesn't have a filter you need, with access to so many available Python modules, you can easily write your own.

```console
Computer:pyspelling facelessuser$ pyspelling
Misspelled words:
<html-content> site/index.html: P
--------------------------------------------------------------------------------
cheking
particularlly
--------------------------------------------------------------------------------

Misspelled words:
<context> pyspelling/__meta__.py(41): Pep440Version
--------------------------------------------------------------------------------
Accessors
accessor
--------------------------------------------------------------------------------

!!!Spelling check failed!!!
```

## Prerequisites

PySpelling is a wrapper around either Aspell or Hunspell. If you do not have a working Aspell or Hunspell on your system, PySpelling will **not** work. It is up to the user to either build locally or acquire via a package manager a working spell checker installation. PySpelling pre-processes files with Python filters, and then sends the resulting text to the preferred spell checker via command line.

## Installing

Installation is easy with pip:

```bash
pip install pyspelling
```

If you want to manually install it, run `#!bash python setup.py build` and `#!bash python setup.py install`.

## Command Line Usage

```
usage: spellcheck [-h] [--version] [--verbose] [--name NAME] [--binary BINARY]
                  [--config CONFIG] [--spellchecker SPELLCHECKER]

Spell checking tool.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --verbose, -v         Verbosity level.
  --name NAME, -n NAME  Specific spelling task by name to run.
  --binary BINARY, -b BINARY
                        Provide path to spell checker's binary.
  --config CONFIG, -c CONFIG
                        Spelling config.
  --spellchecker SPELLCHECKER, -s SPELLCHECKER
                        Choose between aspell and hunspell
```

PySpelling can be run with the command below (assuming your Python bin/script folder is in your path).  By default it will look for the spelling configuration file `.pyspelling.yml`.

```
pyspelling
```

If you have multiple Python versions, you can run the PySpelling associated with that Python version by appending the Python major and minor version:

```
pyspelling3.7
```

To specify a specific configuration other than the default, or even point to a different location:

```
pyspelling -c myconfig.yml
```

To run a specific spelling task in your configuration file by name, you can use the `name` option. You can even specify multiple names if desired:

```
pyspelling -n my_task -n my_task2
```

To run a more verbose output, use the `-v` flag. You can increase verbosity level by including more `v`s: `-vv`.  You can currently go up to four levels.

```
pyspelling -v
```

If the binary for your spell checker is not found in your path, you can provide a path to the binary.

```
pyspelling -b "path/to/aspell"
```

You can specify the spell checker type by specifying it on the command line. PySpelling supports `hunspell` and `aspell`, but defaults to `aspell`. This will override the preferred `spellchecker` setting in the configuration file.

```
pyspelling -s hunspell
```

## Supported Spell Check Versions

PySpelling is tested with Hunspell 1.6+, and recommends using only 1.6 and above. PySpelling is also tested on Aspell 0.60+ (which is recommended), but should also work on the 0.50 series.

## Usage in Windows

If you are dealing with Unicode text, Windows often has difficulty showing it in the console. Using [Windows Unicode Console][win-unicode-console] to patch your Windows install can help. On Python 3.6+ it might not be needed at all. Certain specialty consoles on Windows may report confusing information related to what encoding is used in the console. It is left to the user to resolve console Unicode issues, though proposals for better ways to handle this would be considered.

--8<-- "refs.txt"
