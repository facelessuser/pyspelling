# Filters

## Overview

Filters are objects that take a Unicode string and encoding and return an augmented Unicode string. They can convert the text from one form to another or remove text that is of no interest. Encoding is provided in case you need to convert it back and forth to and from bytes.

## Available Filters

PySpelling comes with a couple of built-in filters.

### Markdown

The Markdown filter passes a Unicode string through Python Markdown to convert Markdown syntax. The resulting string with be HTML content. It can be included via `pyspelling.filters.markdown_filter`.

### HTML

The HTML filter takes a string and converts it an HTML object using BeautifulSoup4, and then aggregates all text that should be spell checked in a single string.  It can be configured to avoid certain tags, classes, IDs, or other attributes if desired.  It can also be instructed to scan certain tag attributes for content to spell check. It can be included via `pyspelling.filters.html_filter`.

### Context

The Context filter is used to create context delimiters for filter content you want and don't want. Delimiters are defined in pairs, and depending on how the filter is configured, the opening delimiter will swap from ignoring text to gathering text and when the closing delimiter is met, it will swap back from gathering text to ignoring text.  If `context_visible_first` is set to `true`, the logic will be reversed. The filter can be included via `pyspelling.filters.context_filter`.

### Writing a Filter

Under construction.
