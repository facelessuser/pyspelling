# PySpelling

!!! warning "Documents Under Construction"
    This project is in the early alpha stage. Features may be in flux, and documentation may be incomplete and/or changing.  Use at your own risk.

## Overview

PySpelling is a module to help with automating spell checking with [Aspell][aspell] or [Hunspell][hunspell]. It is essentially a wrapper around the command line utility of spell checkers, and allows you to setup different spelling tasks for different file types and filter the content as needed. It also allows you to do more advanced filtering of text via plugins since Aspell's and Hunspell's ability to filter are limited to a handful of types with limited options.

PySpelling is not designed to auto replace misspelled words or have interactive replace sessions, there are already modules to do that. PySpelling is mainly meant to help automate reporting of spelling issues in different file types. So if you are looking for a find and replace spelling tool, this isn't for you.

## Motivation

Aspell and Hunspell are very good spell checking tools. Aspell particularly comes with various filters, but the filters are limited in types and aren't extremely flexible. I mainly wanted to provide an automated spell check tool that I could run locally and in continuous integration environments like Travis CI. Scanning HTML was sometimes frustrating as I would want to simply ignore a tag with a specific class. I could've wrapped my content in something like `<nospell></nospell>`, but since my document sources are in Markdown, it would dirty up the Markdown source. Directly spell checking the Markdown was was even more difficult to the nature of the Markdown syntax.

PySpelling was created to work around Aspell's and Hunspell's search shortcomings by creating a wrapper around them that could be extended to handle more advanced kinds of situations. If I want to filter out specific HTML tags with specific IDs or class names, PySpelling can do it. If I want to scan Python files for docstrings, but also avoid content within a docstring that is wrapped in backticks, I can do that. Additionally, you can leverage existing Python modules that are already highly aware of certain file type's context to save yourself the effort of writing complex lexers and parsers.

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

PySpelling can be run with the command below.  By default it will look for the spelling configuration file at `./.spelling.yml`.

```
pyspelling
```

or

```
python -m pyspelling
```

To specify a specific configuration file:

```
pyspelling -c myconfig.yml
```

To run a spelling task by name:

```
pyspelling -n my_task
```

To run a more verbose output, use the `-v` flag. You can increase verbosity level by including more `v`: `-vv`.  You can currently go up to about three levels.

```
pyspelling -v
```

If the binary for your spell checker is not found in your path, you can provide a path to the binary.

```
pyspelling -b "path/to/aspell"
```

You can specify the spell checker type by specifying it on the command line. PySpelling supports `hunspell` and `aspell`, but defaults to `aspell`.

```
pyspelling -s hunspell
```

## Configuring

PySpelling requires a YAML configuration file. All spelling tasks are defined under the key `documents`.

```yaml
documents:
- task1

- task2
```

Each task requires, at the very least, a `name` for the tasks (while it doesn't enforce a unique name, it should be a unique name) and `sources` to search. If no filter is added, the `pyspelling.filters.text` filter will be used.

```yaml
documents:
- name: Python Source
  sources:
  - pyspelling/**/*.py
```

But if needed, you can configure more complex setup including your own custom word list, specific filters, etc.

```yaml
documents:
- name: Python Source
  sources:
  - pyspelling/**/*.py
  aspell:
    lang: en
  dictionary:
    lang: en
    wordlists:
    - docs/src/dictionary/en-custom.txt
    output: build/dictionary/python.dic
  filters:
  - pyspelling.filters.python:
      strings: false
      comments: false
  - pyspelling.filters.context:
      context_visible_first: true
      escapes: \\[\\`~]
      delimiters:
      - open: (?P<open>`+)
        content: .*?
        close: (?P=open)
      - open: (?s)^(?P<open>\s*~{3,})
        content: .*?
        close: ^(?P=open)
```

### Name

Each spelling tasks *should* have a unique name. This is defined with the `name` key.

```yaml
documents:
- name: Python Source
```

Notice that `file_patterns` should be an array of values.

### Default Encoding

When parsing a file, PySpelling only checks for low hanging fruit that it has 100% confidence in, such as UTF BOMs, and depending on the file parser, there may be additional logic like the file type's encoding declaration in the file header. If there is no BOM, encoding declaration, or other special logic, PySpelling will use the default encoding specified by the first filter which will initially parse the file. Depending on the file type, this could differ, but if you specify no filter, the `text` filter will be used which has a default of `utf-8` as the fallback. You can override the fallback with `default_encoding`:

```yaml
- name: Markdown
  filters:
    - pyspelling.filters.text
  sources:
    - '**/*.md'
  default_encoding: utf-8
```

Keep in mind that the encoding of the file gets passed to the spell checker. They are limited to very specific encodings, so if your file is using an unsupported encoding, it will fail. PySpelling *should* properly convert your encoding name (assuming the encoding is valid for the spellchecker) into an alias that is acceptable. So if you specify `latin-1`, PySpelling will send it as `iso8859-1`.

If you really need advanced encoding detection, you could easily enough write you own filter plugin that utilizes `chardet` or `cchardet` etc.

### Sources

Each spelling task must define sources to search via the `sources` key. Each source should be a wildcard pattern that should match one or more files. PySpelling will iterate these sources performing a glob to determine which files should be spell checked. You can also have multiple patterns on one line that will be considered simultaneously if they are separated with `|`.  This is useful if you'd like to provide an exclusion pattern along with your file pattern. For instance, if we wanted to scan all python files in our folder, but exclude any in the build folder, we could provide the following pattern: `**/*.py|!build/**`.

PySpelling uses [Wildcard Match's `glob` library](https://facelessuser.github.io/wcmatch/glob/) to perform the file searching.  By default, it uses the `NEGATE`, `GLOBSTAR`, and `BRACE` flags, but you can override the flag options with the `glob_flags` option.

```yaml
- name: Python Source
  filters:
    - pyspelling.parsers.python_parser:
        strings: false
        comments: false
  glob_flags: N|G|B
  sources:
  - pyspelling/**/*.py
```

### Filters

Some times your may want to take a buffer and run it through a filter or even multiple filters. Filters operate directly on a text buffer returning the altered text and can be chained together.  Each filter takes the text from the previous, alters it, and passes it on to the next.

Let's say you had some Markdown files and wanted to convert them to HTML, and then filter out specific tags. You could just use the Markdown parser and then filter it through the HTML filter.


```yaml
- name: Markdown
  sources:
  - README.md
  filters:
  - pyspelling.filters.markdown_filter:
  - pyspelling.filters.html_filter:
      comments: false
      attributes:
      - title
      - alt
      ignores:
      - code
      - pre
```

### Personal Dictionaries/Word Lists

When spell checking a document, sometimes you'll have words that are not in your default, installed dictionary. PySpelling automates compiling your own personal dictionary from a list of word lists.

There are two things that must be defined: the default dictionary via the the `lang` option, and `wordlists` which is an array of word lists.  Optionally, you can also define the output location and file name for the compiled dictionary. PySpelling will add the output dictionary via the appropriate method for the spell checker.

```yaml
documents:
- name: Python Source
  sources:
  - pyspelling/**/*.py
  aspell:
    lang: en
  dictionary:
    lang: en
    wordlists:
    - docs/src/dictionary/en-custom.txt
    output: build/dictionary/python.dic
  filters:
  - pyspelling.filters.python:
      strings: false
      comments: false
```

### Aspell Options

Though PySpelling is a wrapper, you can still set a number of Aspell's or Hunspell's options directly, such as default dictionary, search options, and filters. Basically, relevant search options are passed directly to the spell checker, while others are ignored, like replace options (which aren't relevant in PySpelling) and encoding (which are handled internally by PySpelling).

To configure an Aspell option, just configure the desired options under the `aspell` key minus the leading dashes. Hunspell options would be defined under `hunspell`. So `-H` would simply be `H` and `--lang` would be `lang`.

Boolean flags would be set to `true`.

```yaml
documents:
- name: HTML
  sources:
  - docs/**/*.html
  aspell:
    H: true
  filters:
  - pyspelling.filters.html
```


Other options would be set to a string or an integer value (integers would be converted over to a string internally).

```yaml
documents:
- name: Python Source
  sources:
  - pyspelling/**/*.py
  aspell:
    lang: en
  filters:
  - pyspelling.filters.python:
      strings: false
      comments: false
```

Lastly, if you have an option that can be used multiple times, just set the value up as an array, and the option will be added for each value in the array:

```yaml
documents:
- name: Python Source
  sources:
  - pyspelling/**/*.py
  aspell:
    add-extra-dicts:
    - my-dictionary.dic
    - my-other-dictionary.dic
  filters:
  - pyspelling.filters.python:
      strings: false
      comments: false
```

Output:

```
aspell --add-extra-dicts my-dictionary.doc --add-extra-dicts my-other-dictionary.dic
```

--8<-- "refs.txt"
