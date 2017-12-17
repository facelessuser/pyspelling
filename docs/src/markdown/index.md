# PySpelling

!!! warning "Documents Under Construction"
    This project is in the early alpha stage. Features may be in flux, and documentation may be incomplete and/or changing.  Use at your own risk.

## Overview

PySpelling is a module to help with automating spell checking with [Aspell][aspell]. You can setup different spelling tasks for different file types and filter the content as needed.

PySpelling is not designed to auto replace misspelled words or have interactive replace sessions, there are already modules to do that. PySpelling is mainly meant automate reporting of spelling issues in different file types. So if you are looking for a find and replace spelling tool, this isn't for you.

PySpelling allows you to create a configuration file with different spelling tasks.  Each spelling task defines a file parser, files or folders to search, additional filters to apply, personal dictionaries to use etc. You can have as many different spelling tasks as you like covering a variety of different file types.  When run, PySpelling will iterate through all of them report the misspellings found.

## Motivation

Aspell is a very good spell check tool that comes with various filters, but the filters aren't as flexible as I would have liked, and are limited to what is shipped with the tool. I mainly wanted to provide an automated spell check tool that I could run locally and in continuous integration environments like Travis CI. But configuring Aspell to only scan what I wanted was awkward at times.  I use Markdown for documents, and they get converted to HTML. Scanning Markdown directly can pick up lots of content I didn't want to spell check, and can be awkward to try and configure context filters via Aspell to avoid all said content, so HTML was better. Unfortunately, Aspell's ability to filter tags is limited to tag names, and cannot avoid specific attributes like classes, so I had dirty my Markdown syntax at times by wrapping content in `<nospell>` tags which was undesirable.

PySpelling was created to work around Aspell's searching shortcomings by creating a wrapper around Aspell that could be extended to handle more advanced kinds of situations. If I wanted to filter out specific HTML tags with specific IDs or class names, PySpelling can do it. If I want to scan Python files for docstrings, but also avoid content within a docstring that is wrapped in backticks, I can do that. Additionally, I wanted to leverage existing modules that are already highly aware of certain file type's context to save me from writing complex lexers and parsers.  The sacrifice is fine tracking of where a misspelled word is ans many of the libraries augment the buffer under search, but all I care about is what words in a file are misspelled.

For instance, it's much easier to spell check a Markdown file once it is in HTML form.  Instead of being aware of all the different Markdown syntax, you HTML is just tags. So converting Markdown to HTML, and then scanning the HTML is a much easier filtering process. But because the entire buffer is augmented in translation, history of lines and column positions is lost in conversion, but since all I want to do is identify the words, losing that history is okay. PySpelling allows you to create plugins that leverage existing Python Modules for parsing a file's context so you don't have to write your own elaborate parser unless you want to. To parse HTML, you can just run it through BeatifulSoup, lxml, or whatever else you prefer.

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

Each task requires, at the very least, a `name` for the tasks, a `parser`, and `src`s to search.

```yaml
documents:
- name: Python Source
  parser: pyspelling.parsers.python_parser
  src:
  - pyspelling
```

But if needed, you can configure more complex setup:

```yaml
documents:
- name: Python Source
  parser: pyspelling.parsers.python_parser
  options:
    strings: false
    comments: false
  src:
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

Each spelling tasks needs a name, this is defined with the `name` key.

```yaml
documents:
- name: Python Source
```

### Parser

Spelling tasks need to specify a file parser to use for the files in a given task. This is done via the `parser` option. Parsers are plugins for the PySpelling that will determine the encoding for a file and then parse the content into relevant Unicode text chunks to search.  The configuration value is a string that references the Python import path for the given plugin.  To reference the default Python file parser, which is located at `pyspelling.parsers.python_parser`, the following would be used:

```yaml
documents:
- name: Python Source
  parser: pyspelling.parsers.python_parser
```

If you use the `pyspelling.parsers.raw_parser`, the encoding will be resolved, but the text will be read in as bytes and will be sent directly to Aspell bypassing any PySpelling filters, but you can still configure Aspell to use its filters.

### Parser Options

Depending on the specified parser, there may be specific options that can be configured. For instance, in the default Python parser, we can configure it to only parse docstrings by disabling comments and strings:

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

### Encoding

When parsing a file, PySpelling only checks for low hanging fruit that it has 100% confidence in, such as UTF BOMs, and depending on the file parser, the file type's encoding declaration in the header (if applicable). If there is no BOM or encoding declaration, PySpelling will usually default to 'ASCII' as the fallback, but you can override the fallback with `default_encoding`:

```yaml
- name: Markdown
  file_patterns:
  - '*.md'
  parser: pyspelling.parsers.text_parser
  default_encoding: utf-8
```

!!! note "Note"
    Keep in mind, a file parser may ignore the default encoding if it makes sense.  For instance, Python code, per the specifications, assumes the file to be ASCII unless a UTF BOM or encoding deceleration is defined in the header.  The Python parser will ignore `default_encoding` in order to adhere to the that file's specification.

### Sources

Each spelling task must define sources to search via the `src` key. Each source can either be a file, or a folder (folders will be recursively searched for valid files). PySpelling will iterate these sources matching the files against the file patterns in `extensions`:

```yaml
- name: Python Source
  parser: pyspelling.parsers.python_parser
  options:
    strings: false
    comments: false
  src:
  - pyspelling
```

### Excludes

Sometimes when searching folders, you'll need to exclude certain files and folders.  PySpelling allows you to define wildcard excludes:

```yaml
- name: Python Source
  parser: pyspelling.parsers.python_parser
  src:
  - pyspelling
  excludes:
  - pyspelling/subfolder/*
```

If wildcard patterns are not sufficient, you can also use regular expression:

```yaml
- name: Python Source
  parser: pyspelling.parsers.python_parser
  src:
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
  src:
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
  src:
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
  src:
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
  src:
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
  src:
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
