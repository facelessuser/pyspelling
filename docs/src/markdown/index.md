# Setup &amp; Overview

PySpelling is a module to help with automating spell checking in a project with [Aspell][aspell] or
[Hunspell][hunspell]. It is essentially a wrapper around the command line utility of these two spell checking tools,
and allows you to setup different spelling tasks for different file types. You can apply specific and different filters
and options to each task. PySpelling can also be used in CI environments to fail the build if there are misspelled
words.

Aspell and Hunspell are very good spell checking tools. Aspell particularly comes with a couple of filters, but the
filters are limited in types and aren't extremely flexible. PySpelling was created to work around Aspell's and
Hunspell's filtering shortcomings by creating a wrapper around them that could be extended to handle more kinds of file
formats and provide more advanced filtering. If you need to filter out specific HTML tags with specific IDs or class
names, PySpelling can do it. If you want to scan Python files for docstrings, but also avoid specific content within the
docstring, you can do that as well. If PySpelling doesn't have a filter you need, with access to so many available
Python modules, you can easily write your own.

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

PySpelling is a wrapper around either Aspell or Hunspell. If you do not have a working Aspell or Hunspell on your
system, PySpelling will **not** work. It is up to the user to either build locally or acquire via a package manager a
working spell checker installation. PySpelling pre-processes files with Python filters, and then sends the resulting
text to the preferred spell checker via command line.

## Installing

Installation is easy with pip:

```shell-session
$ pip install pyspelling
```

If you want to manually install it, run `#!bash python setup.py build` and `#!bash python setup.py install`.

## Command Line Usage

```
usage: pyspelling [-h] [--version] [--verbose] [--name NAME | --group GROUP] [--binary BINARY] [--jobs JOBS] [--config CONFIG] [--source SOURCE]
                  [--spellchecker SPELLCHECKER] [--skip-dict-compile]

Spell checking tool.

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --verbose, -v         Verbosity level.
  --name, -n NAME       Specific spelling task by name to run.
  --group, -g GROUP     Specific spelling task group to run.
  --binary, -b BINARY   Provide path to spell checker's binary.
  --jobs, -j JOBS       Specify the number of spell checker processes to run in parallel. Using 0 will utilize the maximum number of cores.
  --config, -c CONFIG   Spelling config.
  --source, -S SOURCE   Specify override file pattern. Only applicable when specifying exactly one --name.
  --spellchecker, -s SPELLCHECKER
                        Choose between aspell and hunspell.
  --skip-dict-compile, -x
                        Skip dictionary compilation if the compiled file already exists.
```

PySpelling can be run with the command below (assuming your Python bin/script folder is in your path).  By default it
will look for the spelling configuration file `.pyspelling.yml`.

```shell-session
$ pyspelling
```

If you have multiple Python versions, you can run the PySpelling associated with that Python version by appending the
Python major and minor version:

```shell-session
$ pyspelling3.11
```

To specify a specific configuration other than the default, or even point to a different location:

```shell-session
$ pyspelling -c myconfig.yml
```

To run a specific spelling task in your configuration file by name, you can use the `name` option. You can even specify
multiple names if desired. You cannot use `name` and `group` together:

```shell-session
$ pyspelling -n my_task -n my_task2
```

If you've specified groups for your tasks, you can run all tasks in a group with the `group` option. You can specify
multiple groups if desired. You cannot use `name` and `group` together.

```shell-session
$ pyspelling -g my_group -g my_group2
```

If you've specified exactly one name via the `name` option, you can override that named task's source patterns with the
`source` option. You can specify multiple `source` patterns if desired.

```shell-session
$ pyspelling -n my_task -S "this/specific/file.txt" -S "these/specific/files_{a,b}.txt"
```

To run a more verbose output, use the `-v` flag. You can increase verbosity level by including more `v`s: `-vv`.  You
can currently go up to four levels.

```shell-session
$ pyspelling -v
```

If the binary for your spell checker is not found in your path, you can provide a path to the binary.

```shell-session
$ pyspelling -b "path/to/aspell"
```

You can specify the spell checker type by specifying it on the command line. PySpelling supports `hunspell` and
`aspell`, but defaults to `aspell`. This will override the preferred `spellchecker` setting in the configuration file.

```shell-session
$ pyspelling -s hunspell
```

To run multiple jobs in parallel, you can use the `--job` or `-j` option. Processing files in parallel can speed up
processing time. Specifying jobs on the command line will override the `jobs` setting in the configuration file.

```console
$ pyspelling -n my_task -j 4
```

/// new | New 2.10
Parallel processing is new in 2.10.
///

## Supported Spell Check Versions

PySpelling is tested with Hunspell 1.6+, and recommends using only 1.6 and above. Some lower versions might work, but
none have been tested, and related issues will probably not be addressed.

I usually patch the English Hunspell dictionary that I use to add apostrophes, if not present. Apostrophe support is a
must for me. I also prefer to not include numbers as word characters (like Aspell) does as I find them problematic, but
this is just my personal preference. Below is a patch I use on an OpenOffice dictionary set
([`git://anongit.freedesktop.org/libreoffice/dictionaries`](https://anongit.freedesktop.org/git/libreoffice/dictionaries.git/)).

```diff
diff --git a/en/en_US.aff b/en/en_US.aff
index d0cccb3..4258f85 100644
--- a/en/en_US.aff
+++ b/en/en_US.aff
@@ -14,7 +14,7 @@ ONLYINCOMPOUND c
 COMPOUNDRULE 2
 COMPOUNDRULE n*1t
 COMPOUNDRULE n*mp
-WORDCHARS 0123456789
+WORDCHARS ’

 PFX A Y 1
 PFX A   0     re   
```

PySpelling is also tested on Aspell 0.60+ (which is recommended), but should also work on the 0.50 series. 0.60+ is
recommended as spell checking is better in the 0.60 series.

PySpelling disables all native Aspell filters by default. If you need to enable Aspell's native filters, you can do so
via Aspell's builtin options. For more information, see
[Aspell configuration options](./configuration.md#spell-checker-options).

/// new | New in 2.4.0
Starting in 2.4.0, PySpelling ensures filters that are native to the spell checker are disabled by default.
///

## Usage in Linux

Aspell and Hunspell is most likely available in your distro's package manager. You need to install both the spell
checker and the dictionaries, or provide your own custom dictionaries. The option to build manually is always available
as well. See your preferred spell checker's manual for more information on building manually.

Ubuntu Aspell install example:

```shell-session
$ sudo apt-get install aspell aspell-en
```

Ubuntu Hunspell install example:

```shell-session
$ sudo apt-get install hunspell hunspell-en-us
```

## Usage in macOS

Aspell and Hunspell can be included via package managers such as Homebrew. You need to install both the spell checker
and the dictionaries, or provide your own custom dictionaries. The option to build manually is always available as well.
See your preferred spell checker's manual for more information on building manually.

Homebrew Aspell install examples:

```shell-session
$ brew install aspell
```

Homebrew Hunspell install examples:

```shell-session
$ brew install hunspell
```

Don't forget to download dictionaries and put them to `/Library/Spelling/`.

## Usage in Windows

Installing Aspell and/or Hunspell in Windows is traditionally done through either a Cygwin or MSYS2/MinGW environment.
If using MYSYS2/MinGW, you can usually install both packages via Pacman. You need to install both the spell checker and
the dictionaries, or provide your own custom dictionaries. The option to build manually is always available as well. See
your preferred spell checker's manual for more information on building manually.

Pacman Aspell install example:

```shell-session
$ pacman -S mingw-w64-x86_64-aspell mingw-w64-x86_64-aspell-en
```

For Aspell, it has been noted that the way the default configuration is configured, builtin Aspell filters are often
inaccessible as the configuration seems to configure paths with mixed, incompatible slash style (backslash and forward
slash). By creating your own override configuration, and using forward slashes only can fix the issue. You must manually
specify a proper `data-dir` and `dict-dir` override path.  This is done in our `appveyor.yml` file for our own personal
tests, so you can check it out to see what is done. After fixing the configuration file, you should have everything
working.

Pacman Hunspell install example:

```shell-session
$ pacman -S mingw-w64-x86_64-hunspell mingw-w64-x86_64-hunspell-en
```

If you are dealing with Unicode text, Windows often has difficulty showing it in the console. Using
[Windows Unicode Console][win-unicode-console] to patch your Windows install can help. On Python 3.6+ it might not be
needed at all. Certain specialty consoles on Windows may report confusing information related to what encoding is used
in the console. It is left to the user to resolve console Unicode issues, though proposals for better ways to handle
this would be considered.

Alternatively, you can just setup PySpelling in a [Windows Subsystem for Linux][wsl] environment and just use the
[Linux instructions](#usage-in-linux).

## Usage in CI

PySpelling was originally written so that it could be used to automate tests in a CI environment. Any automated CI
can use PySpelling assuming the environment is setup appropriately. On most systems it can be pretty straight forward,
on systems like Windows, it may be a bit more complicated as you will have to also setup a Cygwin, MSYS2/MinGW, Windows
Subsystem for Linux environment.

We won't go into all possible CI environments in this documentation, but we will cover how to get PySpelling up and
running on GitHub's CI environment. In the past, PySpelling has successfully been used in Travis CI, AppVeyor, and many
others.

In order to get running in GitHub's CI, you can follow the steps below:

1.  Create a `spelling` task under `jobs`.
2.  Specify a Linux environment as it is one of the easiest to configure and get running.
3.  Use the `actions/checkout` action to checkout your project.
4.  Setup your Python environment using the `actions/setup-python` action.
5.  Install dependencies you may need. Below, we update `pip` and `setuptools` and install `pyspelling`. You may require
    additional dependencies depending on spelling extensions used, or if pre-building of documents is needed.
6.  Install Aspell and Aspell dictionaries. You are also free to use Hunspell if preferred.
7.  Below we've allowed for a `Build documents` step where you can build documentation or do any other file
    preprocessing that is required for your specific environment.
8.  Lastly, run PySpelling.

```yaml
jobs:
  spelling:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v1
    - name: Set up Python 3.7
      uses: actions/setup-python@v1
      with:
        python-version: 3.7
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip setuptools
        python -m pip install pyspelling
        # Install any additional libraries required: additional plugins, documentation building libraries, etc.
    - name: Install Aspell
      run: |
        sudo apt-get install aspell aspell-en
    - name: Build documents
      run: |
        # Perform any documentation building that might be required
    - name: Spell check
      run: |
        python -m pyspelling
```

In *this* project, we actually use `tox` to make running our tests locally and in CI easier. If you would like to use
`tox` as well, you can check out how this project does it by taking a look at the source.

## Usage as `pre-commit` Hook

PySpelling can be used as a [`pre-commit`](https://pre-commit.com/) hook. To use it as a `pre-commit` hook, please have a
look at the following example `.pre-commit-config.yaml`:

```yaml
---
repos:
  - repo: 'https://github.com/facelessuser/pyspelling.git'
    rev: '2.11'
    hooks:
      - id: 'pyspelling'
        verbose: true
        pass_filenames: false
...
```

Please note that version tags should be preferred over using the `master` branch as revision (`rev`) attribute, as the
`master` branch is considered unstable.
