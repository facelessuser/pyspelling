# Filters

## Overview

Filters are objects that take a Unicode string and encoding and return an augmented Unicode string. They can convert the text from one form to another or remove text that is of no interest. Encoding is provided in case you need to convert it back and forth to and from bytes.

## Available Filters

PySpelling comes with a couple of built-in filters.

All filters have the reserved option called `disallow` which allows the user to specify named chunks to avoid. Each parser returns chunks as `SourceText` objects which have an attribute called `name`. `disallow` should be a list of `SourceText` names to avoid.

### Markdown

The Markdown filter passes a Unicode string through Python Markdown to convert Markdown syntax. The resulting string with be HTML content. It can be included via `pyspelling.filters.markdown_filter`.

Options               | Type          | Defaults     | Description
--------------------- | ------------- | ------------ | -----------
`disallow`            | [string]      | `#!py3 []`   | `SourceText` names to avoid processing.
`markdown_extensions` | [string/dict] | `#!py3 []`   | A list of strings defining markdown extensions to use. You can substitute the string with a dict that defines the extension as the key and the value as a dictionary of options.

```yaml
- name: Markdown
  file_patterns:
  - '*.md'
  parser: pyspelling.parsers.text_parser
  sources:
  - README.md
  default_encoding: utf-8
  filters:
  - pyspelling.filters.markdown_filter:
      markdown_extensions:
      - markdown.extensions.toc:
          slugify: !!python/name:pymdownx.slugs.uslugify
          permalink: "\ue157"
      - markdown.extensions.admonition
      - markdown.extensions.smarty
```

### HTML

The HTML filter takes a string and converts it an HTML object using BeautifulSoup4, and then aggregates all text that should be spell checked in a single string.  It can be configured to avoid certain tags, classes, IDs, or other attributes if desired.  It can also be instructed to scan certain tag attributes for content to spell check. It can be included via `pyspelling.filters.html_filter`.

Options      | Type     | Defaults     | Description
------------ | -------- | ------------ | -----------
`disallow`   | [string] | `#!py3 []`   | `SourceText` names to avoid processing.
`comments`   | bool     | `#!py3 True` | Include comment text in the output.
`attributes` | [string] | `#!py3 []`   | Attributes whose content should be included in the output.
`ignores`    | [string] | `#!py3 []`   | Simple selectors that identify tags to ignore. Only allows tags, IDs, classes, and other attributes.

```yaml
- name: markdown
  parser: pyspelling.parsers.markdown_parser
  sources:
  - README.md
  filters:
  - pyspelling.filters.html_filter:
      comments: false
      attributes:
      - title
      - alt
      ignores:
      - code
      - pre
```

### Context

The Context filter is used to create regular expression context delimiters for filtering content you want and don't want. Delimiters are defined in pairs, and depending on how the filter is configured, the opening delimiter will swap from ignoring text to gathering text and when the closing delimiter is met, it will swap back from gathering text to ignoring text.  If `context_visible_first` is set to `true`, the logic will be reversed.

Regular expressions are compiled with the MULTILINE flag so that `^` represents the start of a line and `$` represents the end of a line. `\A` and `\Z` would represent the start and end of the buffer.

You are able to define general escape patterns to prevent escaped delimiters from being captured. Delimiters entries will have an opening, content (to allow a special pattern to represent inter-content escapes), and closing patterns. Closing and content can see flags and groups in prior parts. So if you set a case insensitive flag in the opening, it applies to content and closing as well.

The filter can be included via `pyspelling.filters.context_filter`.

Options                 | Type     | Default       | Description
----------------------- | -------- | ------------- | -----------
`disallow`              | [string] | `#!py3 []`    | `SourceText` names to avoid processing.
`escapes`               | string   | `#!py3 ''`    | Regular expression pattern for character escapes outside delimiters.
`context_visible_first` | bool     | `#!py3 False` | Context will start as invisible and will be invisible between delimiters.
`delimiters`            | [dict]   | `#!py3 []`    | A list of dicts that define the regular expression delimiters.

```yaml
- name: python
  parser: pyspelling.parsers.python_parser
  options:
    strings: false
    comments: false
  sources:
  - pyspelling
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
        close: ^(?P=open)$
```

### Writing a Filter

writing a filter is pretty easy, and the class itself is pretty basic. To handle options, you'll want to override `__init__`, and then the override `filter` to do the actual filtering.  Remember to provide the function `get_filter` so that the PySpelling can easily get your class.

```py3
from pyspelling.filters import Filter

class MyFilter(Filter):
    """My filter class."""

    def __init__(self, options):
        """
        Handle options.

        options:  Dictionary of options.
        """
        super(MyFilter, self).__init__(options)

    def filter(self, text, encoding):
        """
        Filter the text.

        text:     Unicode string.
        encoding: Original text encoding.

        Return:   Unicode string.
        """

        return text


def get_filter():
    """Return the filter."""

    return MyFilter
```
