# PySpelling

!!! warning "Documents Under Construction"
    This project is in the early alpha stage. Features may be in flux, and documentation may be incomplete and/or changing.  Use at your own risk.

## Overview

PySpelling is a module to help with automating spell checking with [Aspell][aspell]. It is essentially a wrapper around the Aspell command line utility, and allows you to setup different spelling tasks for different file types and filter the content as needed. It also allows you to do more advancing filtering of text via plugins since Aspell's filters are limited to a handful of types with limited options.

PySpelling is not designed to auto replace misspelled words or have interactive replace sessions, there are already modules to do that. PySpelling is mainly meant automate reporting of spelling issues in different file types. So if you are looking for a find and replace spelling tool, this isn't for you.

## Motivation

Aspell is a very good spell check tool that comes with various filters, but the filters are limited in types and aren't as flexible as I would have liked. I mainly wanted to provide an automated spell check tool that I could run locally and in continuous integration environments like Travis CI. Scanning HTML was sometimes frustrating as I would want to simply ignore a tag with a specific class. Yes you can wrap your content in something like `<nospell></nospell>`, but since my document sources are in Markdown, it would dirty up my Markdown source, and directly spell checking the Markdown was quite a bit more difficult to ignore types of content.

PySpelling was created to work around Aspell's searching shortcomings by creating a wrapper around Aspell that could be extended to handle more advanced kinds of situations. If I wanted to filter out specific HTML tags with specific IDs or class names, PySpelling can do it. If I want to scan Python files for docstrings, but also avoid content within a docstring that is wrapped in backticks, I can do that. Additionally, I wanted to leverage existing Python modules that are already highly aware of certain file type's context to save me from writing complex lexers and parsers.  The sacrifice is fine tracking of where a misspelled word is and many of the libraries augment the buffer under search, but all I care about is what words in a file are misspelled. So with PySpelling, I can quickly write a plugin to parse a file or filter the content in an automated process.

## Installing

Installation is easy with pip:

```bash
pip install pyspelling
```

If you want to manually install it, run `#!bash python setup.py build` and `#!bash python setup.py install`.

## Command Line Usage

```
usage: spellcheck [-h] [--version] [--verbose] [--name NAME] [--config CONFIG]

Spell checking tool.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --verbose, -v         Verbosity level.
  --name NAME, -n NAME  Specific spelling task by name to run.
  --config CONFIG, -c CONFIG
                        Spelling config.
```

PySpelling can be run with the command below.  By default it will look for the spelling configuration file at `./.spelling.yml`.

```
python -m pyspelling
```

To specify a specific configuration file:

```
python -m pyspelling -c myconfig.yml
```

To run a spelling task by name:

```
python -m pyspelling -n my_task
```

To run a more verbose output, use the `-v` flag. You can increase verbosity level by including more `v`: `-vv`.  You can currently go up to about three levels.

```
python -m pyspelling -v
```

## Configuring

PySpelling requires a YAML configuration file. All spelling tasks are defined under the key `documents`.

```yaml
documents:
- task1

- task2
```

Each task requires, at the very least, a `name` for the tasks (while it doesn't enforce a unique name, it should be a unique name), a `parser`, and `sources` to search.

```yaml
documents:
- name: Python Source
  parser: pyspelling.parsers.python_parser
  sources:
  - pyspelling
```

But if needed, you can configure more complex setup including your own custom word list, additional filters, etc.

```yaml
documents:
- name: Python Source
  parser: pyspelling.parsers.python_parser
  options:
    strings: false
    comments: false
  sources:
  - pyspelling
  aspell:
    lang: en
  dictionary:
    lang: en
    wordlists:
    - docs/src/dictionary/en-custom.txt
    output: build/dictionary/python.dic
  filters:
  - pyspelling.filters.context_filter:
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

### Parser

Spelling tasks need to specify a file parser to use for the files in a given task. This is done via the `parser` option. Parsers are plugins for PySpelling that will determine the encoding for a file and then parse the content into relevant text chunks to search (usually Unicode).  The configuration value is a string that references the Python import path for the given plugin.  To reference the default Python file parser, which is located at `pyspelling.parsers.python_parser`, the following would be used:

```yaml
documents:
- name: Python Source
  parser: pyspelling.parsers.python_parser
```

If you use the `pyspelling.parsers.raw_parser`, the encoding will not be resolved, and instead will use the supplied `default_encoding`. The text will be read in as bytes and will be sent directly to Aspell with the aforementioned default encoding. Since the raw parser stores the text as bytes, the filters will be skipped as they only accept Unicode.

### Parser Options

Depending on the specified parser, there may be specific `options` that can be configured. For instance, in the default Python parser, we can configure it to only parse docstrings by disabling comments and strings:

```yaml
documents:
- name: Python Source
  parser: pyspelling.parsers.python_parser
  options:
    strings: false
    comments: false
```

### File Patterns

A given parser will have a list of valid wildcard file patterns, so when you are searching a folder, you only search the relevant files. If you want to use the parser on a file type that is not currently covered, you can override the file pattern for that parser with the `file_patterns` option. Let's say we wanted to parse file types `*.python` with the Python file parser, you could use:

```yaml
documents:
- name: Python Source
  parser: pyspelling.parsers.python_parser
  file_patterns:
    - '*.python'
```

Notice that `file_patterns` should be an array of values.

### Default Encoding

When parsing a file, PySpelling only checks for low hanging fruit that it has 100% confidence in, such as UTF BOMs, and depending on the file parser, there may be additional logic like the file type's encoding declaration in the file header. If there is no BOM, encoding declaration, or other special logic, PySpelling will usually default to "ASCII" as the fallback, but you can override the fallback with `default_encoding`:

```yaml
- name: Markdown
  file_patterns:
  - '*.md'
  parser: pyspelling.parsers.text_parser
  default_encoding: utf-8
```

Keep in mind that the encoding of the file gets passed to Aspell. Aspell is limited to very specific encodings, so if your file is using an unsupported encoding, it will fail. PySpelling *should* properly convert your encoding name (assuming the encoding is valid for Aspell) into an alias that is acceptable to Aspell. So if you specify `latin-1`, PySpelling will send it to Aspell as `iso8859-1`.

If you really need advanced encoding detection, you could easily enough write you own file parser plugin that utilize `chardet` or `cchardet` etc.

### Sources

Each spelling task must define sources to search via the `sources` key. Each source can either be a file, or a folder (folders will be recursively searched for valid files). PySpelling will iterate these sources matching the files against the file patterns in `extensions`:

```yaml
- name: Python Source
  parser: pyspelling.parsers.python_parser
  options:
    strings: false
    comments: false
  sources:
  - pyspelling
```

### Excludes

Sometimes when searching folders, you'll need to exclude certain files and folders.  PySpelling allows you to define wildcard excludes:

```yaml
- name: Python Source
  parser: pyspelling.parsers.python_parser
  sources:
  - pyspelling
  excludes:
  - pyspelling/subfolder/*
```

If wildcard patterns are not sufficient, you can also use regular expression:

```yaml
- name: Python Source
  parser: pyspelling.parsers.python_parser
  sources:
  - pyspelling
  regex_excludes:
  - pyspelling/(?:folder|other-folder)/.*
```

### Filters

Some times your may want to take a buffer and run it through a filter or filters. Filters operate directly on a text buffer returning the altered text and can be chained together.  Each filter takes the text from the previous, alters it, and passes it on to the next.

Let's say you had some Markdown files and wanted to convert them to HTML, and then filter out specific tags. You could just use the Markdown parser and then filter it through the HTML filter, but to illustrate filter chaining, we'll parse the file as text, and then run it through the markdown filter followed by the HTML filter that will return the content of the tags (and selected attributes) excluding certain selectors.


```yaml
- name: Markdown
  file_patterns:
  - '*.md'
  parser: pyspelling.parsers.text_parser
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
      - a.magiclink-compare
      - a.magiclink-commit
      - span.keys
      - .MathJax_Preview
      - .md-nav__link
      - .md-footer-custom-text
      - .md-source__repository
```

### Personal Dictionaries/Word Lists

When spell checking a document, sometimes you'll have words that are not in your default, installed dictionary. PySpelling automates compiling your own personal dictionary from a list of word lists.

There are two things that must be defined: the default dictionary via the the `lang` option, and `wordlists` which is an array of word lists.  Optionally, you can also define the output location and file name for the compiled dictionary. PySpelling will add the output dictionary via Aspell's `--add-extra-dicts` option automatically.

```yaml
documents:
- name: Python Source
  parser: pyspelling.parsers.python_parser
  options:
    strings: false
    comments: false
  sources:
  - pyspelling
  aspell:
    lang: en
  dictionary:
    lang: en
    wordlists:
    - docs/src/dictionary/en-custom.txt
    output: build/dictionary/python.dic
```

### Aspell Options

Though PySpelling is a wrapper around Aspell, you can still set a number of Aspell's options directly, such as default dictionary, search options, and filters. Basically, relevant search options are passed directly to Aspell, while others are ignored, like Replace options (which aren't relevant in PySpelling) and options like encoding (which are handled internally by PySpelling).

To configure an Aspell option, just configure the desired options under the `aspell` key minus the leading dashes.  So `-H` would simply be `H` and `--lang` would be `lang`.

Boolean flags would be set to `true`.

```yaml
documents:
- name: HTML
  parser: pyspelling.parsers.html_parser
  sources:
  - docs
  aspell:
    H: true
```


Other options would be set to a string or an integer value (integers would be converted over to a string internally).

```yaml
documents:
- name: Python Source
  parser: pyspelling.parsers.python_parser
  options:
    strings: false
    comments: false
  sources:
  - pyspelling
  aspell:
    lang: en
```

Lastly, if you have an option that can be used multiple times, just set the value up as an array, and the option will be added for each value in the array:

```yaml
documents:
- name: Python Source
  parser: pyspelling.parsers.python_parser
  options:
    strings: false
    comments: false
  sources:
  - pyspelling
  aspell:
    add-extra-dicts:
      - my-dictionary.dic
      - my-other-dictionary.dic
```

Output:

```
aspell --add-extra-dicts my-dictionary.doc --add-extra-dicts my-other-dictionary.dic
```

--8<-- "refs.md"
