# PySpelling

!!! warning "Documents Under Construction"
    This project is in the early alpha stage. Features may be in flux, and documentation may be incomplete and/or changing.  Use at your own risk.

## Overview

PySpelling is a module to help with automating spell checking in a project with [Aspell][aspell] or [Hunspell][hunspell]. It is essentially a wrapper around the command line utility of the preferred spell checking tool, and allows you to setup different spelling tasks for different file types and apply filters to the content as needed. PySpelling can also be used in CI environments to fail the build if there are misspelled words.

Aspell and Hunspell are very good spell checking tools. Aspell particularly comes with a couple of filters, but the filters are limited in types and aren't extremely flexible. PySpelling was created to work around Aspell's and Hunspell's filtering shortcomings by creating a wrapper around them that could be extended to handle more advanced kinds text formats and filtering. If you need to filter out specific HTML tags with specific IDs or class names, PySpelling can do it. If you want to scan Python files for docstrings, but also avoid specific content within the docstring, you can do that as well. If PySpelling doesn't have a filter you need, with access to so many available Python modules, you can easily write your own.

PySpelling allows you to define tasks that outline what kind of files you want to spell check, and then sends them down a pipeline that filters the content returning hunks of text with some associated context. Each hunk is sent down each step of the pipeline until it reaches the final step, the spell check step. Between filters, you can inject "flow control" steps that allow you to have certain text hunks skip specific steps.

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

If you have multiple Python versions, you can run the specific version by appending the Python major and minor version:

```
pyspelling3.7
```

To specify a specific configuration other than the default, or even point to a different location:

```
pyspelling -c myconfig.yml
```

To run a specific spelling task in your configuration file by name:

```
pyspelling -n my_task
```

To run a more verbose output, use the `-v` flag. You can increase verbosity level by including more `v`s: `-vv`.  You can currently go up to three levels.

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

## Configuring

PySpelling requires a YAML configuration file. The file defines the various spelling tasks along with their individual filters and options.

All of the tasks are contained under the keyword `matrix` and are organized in a list:

```yaml
matrix:
- task1

- task2
```

Each task requires, at the very least, a `name` and `sources` to search. Depending on your setup, you may need to set the dictionary to use as well.

Each spell checker specifies their dictionary/language differently which is covered in more details in [Spell Checker Options](#spell-checker-options).

```yaml
matrix:
- name: Python Source
  aspell:
    lang: en
  sources:
  - pyspelling/**/*.py
```

You can also define more complicated tasks by providing a custom pipeline.

```yaml
matrix:
- name: Python Source
  sources:
  - pyspelling/**/*.py
  aspell:
    lang: en
  dictionary:
    wordlists:
    - docs/src/dictionary/en-custom.txt
    output: build/dictionary/python.dic
  pipeline:
  - pyspelling.filters.python:
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

Each spelling tasks *should* have a name and is defined with the `name` key.

When using the command line `--name` option, any task with the matching name will be run. Each task can have a unique name, or you can assign multiple tasks with the same name so that you can run them all with the `--name` option.

```yaml
matrix:
- name: Python Source
```

### Default Encoding

When parsing a file, the encoding detection and translation of the data into Unicode is performed by the first filter in the pipeline. For instance, if HTML is the first, it may check for a BOM or look at the file's header to find the `meta` tag that specifies the file's encoding. If all encoding checks fail, the filter will usually apply an appropriate default encoding for the file content type (usually UTF-8, but check the specific filters documentation to be sure). If needed, the filter's default encoding can be overridden in the task via the `default_encoding` key. After the first step in the pipeline, the text is passed around as Unicode which requires no Unicode detection.

```yaml
matrix:
- name: markdown
  pipeline:
  - pyspelling.filters.text
  sources:
  - '**/*.md'
  default_encoding: utf-8
```

Once all filtering is complete, the text will be passed to the spell checker as byte strings, usually with the originally detected encoding (unless a filter specifically alters the encoding). The supported spell checkers are limited to very specific encodings, so if your file is using an unsupported encoding, it will fail.

!!! tip "Unsupported Encodings"
    If you are trying to spell check a file in an unsupported encoding, you can use the builtin text filter to convert the content to a more appropriate encoding. In general, it is recommended to work in, or convert to UTF-8.

### Sources

Each spelling task must define a list of sources to search via the `sources` key. Each source should be a glob pattern that should match one or more files. PySpelling will perform a search with these patterns to determine which files should be spell checked.

You can also have multiple patterns on one line separated with `|`. When multiple patterns are defined like this, they will evaluated simultaneously. This is useful if you'd like to provide an exclusion pattern along with your file pattern. For instance, if we wanted to scan all python files in our folder, but exclude any in the build folder, we could provide the following pattern: `**/*.py|!build/*`.

PySpelling uses [Wildcard Match's `glob` library](https://facelessuser.github.io/wcmatch/glob/) to perform the file searching.  By default, it uses the `NEGATE`, `GLOBSTAR`, and `BRACE` flags, but you can override the flag options with the `glob_flags` option.

```yaml
matrix:
- name: python
  filters:
    - pyspelling.filters.python:
        comments: false
  glob_flags: N|G|B
  sources:
  - pyspelling/**/*.py
```

### Pipeline

Some times you may want to take a buffer and run it through a filter or even multiple filters. Filters are chained together in a pipeline. Text hunks that are returned by one filter are fed down into the next until they reach the spell checker step.  Each filter takes the text from the previous, alters it, and passes it on to the next with some context. To insert a filter, you just provide the import path of the `Filter` plugin.

Let's say you had some Markdown files and wanted to convert them to HTML, and then filter out specific tags. You could just use the Markdown parser and then filter it through the HTML filter.


```yaml
matrix:
- name: markdown
  sources:
  - README.md
  filters:
  - pyspelling.filters.markdown:
  - pyspelling.filters.html:
      comments: false
      attributes:
      - title
      - alt
      ignores:
      - code
      - pre
```

If needed, you can also place "flow control" steps between "filter" steps. Each text hunk that is passed between filters has a category assigned to it from the previous filter. Flow control steps allow you to restrict the next Filter to specific categories, or exclude specific categories from the next step. This is covered in more depth in [Flow Control](./flowcontrol.md).

In the example below, we use the `python` filter to extract comments (category `py-comment`) and docstrings (category `py-docstring`), but then use the `wildcard` "flow control" plugin to restrict the next filter to only `py-comment` hunks by instructing the the "flow control" plugin to have `py-docstring` hunks skip the next step. The last `context` filter will then accept all hunks in the pipeline, including the the `py-comment` hunks that skipped the first `context` filter.

```yaml
matrix:
- name: python
  sources:
  - setup.py
  - pyspelling/**/*.py
  aspell:
    lang: en
  dictionary:
    lang: en
    wordlists:
    - docs/src/dictionary/en-custom.txt
    output: build/dictionary/python.dic
  pipeline:
  - pyspelling.filters.python:
  - pyspelling.flow_control.wildcard:
      skip:
      - py-docstring
  - pyspelling.filters.context:
      context_visible_first: true
      delimiters:
      # Ignore lint (noqa) and coverage (pragma) as well as shebang (#!)
      - open: ^(?:(?:noqa|pragma)\b|!)
        content: .*?
        close: $
      # Ignore Python encoding string -*- encoding stuff -*-
      - open: ^-*-
        content: .*?
        close: -*-$
  - pyspelling.filters.context:
      context_visible_first: true
      escapes: \\[\\`~]
      delimiters:
      # Ignore text between inline back ticks
      - open: (?P<open>`+)
        content: .*?
        close: (?P=open)
      # Ignore multiline content between fences ~~~ content ~~~
      - open: (?s)^(?P<open>\s*~{3,})
        content: .*?
        close: ^(?P=open)$
```

### Dictionaries and Personal Wordlists

By default, PySpelling sets your main dictionary to `en` for Aspell and `en_US` for Hunspell. If you do not desire an American English dictionary, or these dictionaries are not installed in their expected default locations, you will need to configure PySpelling so it can find your preferred dictionary. Since dictionary configuration varies for each spell checker, the main dictionary is configured via [Spell Checker Options](#spell-checker-options).

For Aspell, you would use the command line option `--lang` or `-l`, which in the YAML configuration file is `lang` or `l` respectively:

```yaml
matrix:
- name: python
  aspell:
    lang: en
```

For Hunspell, you would use the command line option `-d`, which in the YAML configuration file is `d`:

```yaml
matrix:
- name: python
  hunspell:
    d: en_US
```

While the dictionaries cover a number of commonly used words, they are usually not sufficient. Luckily, both Aspell and Hunspell allow adding custom wordlists. You can have as many wordlists as you like, and they be included in a list under the key `wordlists` which is also found under the key `dictionary`. While Hunspell doesn't directly compile the wordlists, Aspell does, and it uses the main dictionary that you have specified to accomplish this. All the wordlists are combined into one custom dictionary file whose output name and location is defined via the `output` key which is also found under the `dictionary` key.

```yaml
matrix:
- name: python
  sources:
  - pyspelling/**/*.py
  aspell:
    lang: en
  dictionary:
    wordlists:
    - docs/src/dictionary/en-custom.txt
    output: build/dictionary/python.dic
  pipeline:
  - pyspelling.filters.python:
      comments: false
```

### Spell Checker Options

Since PySpelling is a wrapper around both Aspell and Hunspell, there are a number of spell checker specific options. As only a few options are present in both, it was decided to expose them via spell checker specific keywords: `aspell` and `hunspell` for Aspell and Hunspell respectively. Here is where you can set options like the default dictionary, search options. Not all options are exposed though, only relevant search options are passed directly to the spell checker. Things like replace options (which aren't relevant in PySpelling) and encoding (which are handled internally by PySpelling) are not accessible.

Spell checker specific options basically translate directly to the spell checker's command line options. For instance, a short form option such as `-l` would simply be represented with the keyword `l`, and the long name form of the same option `--lang` would be represented as `lang`.  Following the key, you would provide the appropriate value depending on it's requirement.

Boolean flags would be set to `true`.

```yaml
matrix:
- name: html
  sources:
  - docs/**/*.html
  aspell:
    H: true
  filters:
  - pyspelling.filters.html
```

Other options would be set to a string or an integer value.

```yaml
matrix:
- name: python
  sources:
  - pyspelling/**/*.py
  aspell:
    lang: en
  filters:
  - pyspelling.filters.python:
      strings: false
      comments: false
```

Lastly, if you have an option that can be used multiple times, just set the value up as an array, and the option will be added for each value in the array. Assuming you had multiple pre-compiled dictionaries, you could add them under Aspell's `--add-extra-dicts` option:

```yaml
- name: Python Source
  sources:
  - pyspelling/**/*.py
  aspell:
    add-extra-dicts:
    - my-dictionary.dic
    - my-other-dictionary.dic
  pipeline:
  - pyspelling.filters.python:
      comments: false
```

Which would be equivalent to doing this from the command line:

```
aspell --add-extra-dicts my-dictionary.doc --add-extra-dicts my-other-dictionary.dic
```

--8<-- "refs.txt"
