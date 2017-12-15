# PySpelling

## Overview

PySpelling is a module to help with automating spell checking with Aspell. You can setup different spelling tasks for different file types and filter the content as needed.

PySpelling is not designed to auto replace misspelled words or have interactive replace sessions, there are already modules to do that. PySpelling is mainly meant automate reporting of spelling issues in different file types. So if you are looking for a find and replace spelling tool, this isn't for you.

PySpelling allows you to create a configuration file with different spelling tasks.  Each spelling task defines a file parser, files or folders to search, additional filters to apply, personal dictionaries to use etc. You can have as many different spelling tasks as you like covering a variety of different file types.  When run, PySpelling will iterate through all of them report the misspellings found.

## Motivation

Aspell is a very good spell check tool that comes with various filters, but the filters aren't as flexible as I would have liked, and are limited to what is shipped with the tool. I mainly wanted to provide an automated spell check tool that I could run locally and in continuous integration environments like Travis CI. But configuring Aspell to only scan what I wanted was awkward at times.  I use Markdown for documents, and they get converted to HTML. Scanning Markdown directly can pick up lots of content I didn't want to spell check, and can be awkward to try and configure context filters via Aspell to avoid all said content, so HTML was better. Unfortunately, Aspell's ability to filter tags is limited to tag names, and cannot avoid specific attributes like classes, so I had dirty my Markdown syntax at times by wrapping content in `<nospell>` tags which was undesirable.

PySpelling was created to work around Aspell's searching shortcomings by creating a wrapper around Aspell that could be extended to handle more advanced kinds of situations. If I wanted to filter out specific HTML tags with specific IDs or class names, PySpelling can do it. If I want to scan Python files for docstrings, but also avoid content within a docstring that is wrapped in backticks, I can do that. Additionally, I wanted to leverage existing modules that are already highly aware of certain file type's context to save me from writing complex lexers and parsers.  The sacrifice is fine tracking of where a misspelled word is ans many of the libraries augment the buffer under search, but all I care about is what words in a file are misspelled.

For instance, it's much easier to spell check a Markdown file once it is in HTML form.  Instead of being aware of all the different Markdown syntax, you HTML is just tags. So converting Markdown to HTML, and then scanning the HTML is a much easier filtering process. But because the entire buffer is augmented in translation, history of lines and column positions is lost in conversion, but since all I want to do is identify the words, losing that history is okay. PySpelling allows you to create plugins that leverage existing Python Modules for parsing a file's context so you don't have to write your own elaborate parser unless you want to. To parse HTML, you can just run it through BeatifulSoup, lxml, or whatever else you prefer.

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

Spelling tasks need to specify a file parser to use for the files in a given task. This is done via the `parser` option. Parsers are plugins for the PySpelling that will determine the encoding for a file, and parse the content for relevant text chunks to search.  The value is a string that references the Python import path for the given plugin.  To reference the default Python file parser, which is located at `pyspelling.parsers.python_parser`, the following would be used:

```yaml
documents:
- name: Python Source
  parser: pyspelling.parsers.python_parser
```

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

A given parser will have a list of valid file patterns, so when you are searching a folder, you only search the relevant files. If you want to use the parser on a file type that is not currently covered, you can override the file pattern for that parser with the `file_patterns` option. Let's say we wanted to parse file types `*.python` with the Python file parser, you could use:

```yaml
documents:
- name: Python Source
  parser: pyspelling.parsers.python_parser
  file_patterns:
    - '*.python'
```

Notice that `file_patterns` should be an array of values.

### Encoding

When parsing a file, PySpelling only checks for UTF BOMs, and, depending on the file parser, the file type's encoding declaration in the header (if applicable). If there is no BOM or encoding declaration, PySpelling will usually use 'ASCII' as the fallback, but you can override the fallback with `fallback_encoding`:

```yaml
- name: Markdown
  file_patterns:
  - '*.md'
  parser: pyspelling.parsers.text_parser
  fallback_encoding: utf-8
```

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

### Aspell Options

### Personal Dictionaries/Word Lists

### Filters
