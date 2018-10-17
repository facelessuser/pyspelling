# Filters

## Overview

Filters are chainable PySpelling plugins that filter the content of a buffer and return only the portions that are desired. The portions that are returned are partitioned in to chunks that contain a little contextual information. Some filters may return only one chunk in the list that is the entirety of the file, and some may return context specific chunks: one for each docstring, one for each comment, etc. The metadata associated with each chunk can be used to halt filtering of specific chunks in the chain. Some of the metadata is also used to give feedback to the user when results are displayed.

Each chunk returned by the filter is a `SourceText` object. These objects contain the desired, filtered text from the source along with some metadata: encoding, display context, and a category that describes what kind of text the data is. After all filters have processed the text, each `SourceText` text is finally passed to the spell checker.

The text data in a `SourceText` object is always Unicode, but during the filtering process, the filter can decode the Unicode if required as long as it is returned as Unicode at the end. The first filter in the chain is always responsible for initially reading the file from disk and getting the file content into a Unicode buffer that PySpelling can work with. It is also responsible for identifying encoding from the file header if there is special logic to determine such things.

## Available Filters

PySpelling comes with a couple of built-in filters.

### Text

This is a filter that simply retrieves the buffer's text and returns it as Unicode.  It takes a file or file buffer and returns a single `SourceText` object containing all the text in the file.  It is the default is no filter is specified and can be manually included via `pyspelling.filters.text`. When first in the chain, the file's default, assumed encoding is `utf-8` unless otherwise overridden by the user.

Options               | Type          | Default          | Description
--------------------- | ------------- | ---------------- | -----------
`disallow`            | [string]      | `#!py3 []`       | `SourceText` names to avoid processing.
`normalize`           | string        | `#!py3 ''`       | Performs Unicode normalization. Valid values are `NFC`, `NFD`, `NFKC`, and `NFKD`.
`convert_encoding`    | string        | `#!py3 ''`       | Assuming a valid encoding, the text will be converted to the specified encoding.
`errors`              | string        | `#!py3 'strict'` | Specifies what to do when converting the encoding, and a character can't be converted. Valid values are `strict`, `ignore`, `replace`, `xmlcharrefreplace`, `backslashreplace`, and `namereplace`.

```yaml
- name: Text
  default_encoding: cp1252
  filters:
  - pyspelling.filters.text:
      convert_encoding: utf-8
  source:
  - **/*.txt
```

### Markdown

The Markdown filter converts a text file's buffer using Python Markdown and returns a single `SourceText` object containing the text as HTML. It can be included via `pyspelling.filters.markdown`. When first in the chain, the file's default, assumed encoding is `utf-8` unless otherwise overridden by the user.

Options               | Type          | Default    | Description
--------------------- | ------------- | ---------- | -----------
`disallow`            | [string]      | `#!py3 []` | `SourceText` names to avoid processing.
`markdown_extensions` | [string/dict] | `#!py3 []` | A list of strings defining markdown extensions to use. You can substitute the string with a dict that defines the extension as the key and the value as a dictionary of options.

```yaml
- name: Markdown
  filters:
  - pyspelling.parsers.markdown_parser:
      markdown_extensions:
      - markdown.extensions.toc:
          slugify: !!python/name:pymdownx.slugs.uslugify
          permalink: "\ue157"
      - markdown.extensions.admonition
      - markdown.extensions.smarty
  source:
  - **/*.md
```

### HTML

When first in the chain, the HTML filter will look for the encoding of the HTML in its header and convert the buffer to Unicode. It will assume `utf-8` if no encoding header is found, and the user has not overridden the fallback encoding.

The HTML filter uses BeautifulSoup4 to convert the Unicode content to HTML, and then aggregates all text that should be spell checked in a single `SourceText` object.  It can be configured to avoid certain tags, classes, IDs, or other attributes if desired.  It can also be instructed to scan certain tag attributes for content to spell check. It can be included via `pyspelling.parsers.html_parser`.

Options      | Type     | Default      | Description
------------ | -------- | ------------ | -----------
`disallow`   | [string] | `#!py3 []`   | `SourceText` names to avoid processing.
`comments`   | bool     | `#!py3 True` | Include comment text in the output.
`attributes` | [string] | `#!py3 []`   | Attributes whose content should be included in the output.
`ignores`    | [string] | `#!py3 []`   | Simple selectors that identify tags to ignore. Only allows tags, IDs, classes, and other attributes.

```yaml
- name: mkdocs
  filters:
  - pyspelling.filters.html:
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
      - .headerlink
      - .md-icon
  sources:
  - site/*.html
```

### Python

When first in the chain, the Python filter will look for the encoding of the file in the header, and convert to Unicode accordingly. It will assume `utf-8` if no encoding header is found, and the user has not overridden the fallback encoding.

Text is returned in blocks based on the context of the text.  Each docstring is returned as its own object.  Comments are returned as their own as well as strings. This is in case you do something like write your docstrings in Markdown, you can run each one individually through the Markdown filter, or some other filter if required.

Options          | Type     | Default       | Description
---------------- | -------- | ------------- | -----------
`disallow`       | [string] | `#!py3 []`    | `SourceText` names to avoid processing.
`comments`       | bool     | `#!py3 True`  | Return `SourceText` entries for each comment.
`docstrings`     | bool     | `#!py3 True`  | Return `SourceText` entries for each docstrings.
`strings`        | bool     | `#!py3 False` | Return `SourceText` entries for each string.
`bytes`          | bool     | `#!py3 False` | Return `SourceText` entries for each byte string. Only ASCII content will be included, and encoding will be returned as ASCII.
`group_comments` | bool     | `#!py3 False` | Group consecutive Python comments as one `SourceText` entry.

```yaml
- name: python
  filters:
  - pyspelling.filters.python:
      strings: false
      comments: false
  sources:
  - pyspelling/**/*.py
```

### JavaScript

When first int the chain, the JavaScript filter uses no special encoding detection. It will assume `utf-8` if no encoding BOM is found, and the user has not overridden the fallback encoding. Text is returned in blocks based on the context of the text depending on what is enabled.  The parser can return JSDoc comments, block comments, and/or inline comments. Each is returned as its own object.

Options          | Type     | Default       | Description
---------------- | -------- | ------------- | -----------
`disallow`       | [string] | `#!py3 []`    | `SourceText` names to avoid processing.
`block_comments` | bool     | `#!py3 True`  | Return `SourceText` entries for each block comment.
`line_comments`  | bool     | `#!py3 True`  | Return `SourceText` entries for each line comment.
`jsdocs`         | bool     | `#!py3 False` | Return `SourceText` entries for each JSDoc comment.
`group_comments` | bool     | `#!py3 False` | Group consecutive Python comments as one `SourceText` entry.

```yaml
- name: javascript
  filters:
  - pyspelling.filters.javascript
      jsdocs: true
      line_comments: false
      block_comments: false
  sources:
  - js_files/**/*.js
```

### Context

The Context filter is used to create regular expression context delimiters for filtering content you want and don't want. Delimiters are defined in pairs, and depending on how the filter is configured, the opening delimiter will swap from ignoring text to gathering text. And when the closing delimiter is met, the filter will swap back from gathering text to ignoring text.  If `context_visible_first` is set to `true`, the logic will be reversed.

Regular expressions are compiled with the MULTILINE flag so that `^` represents the start of a line and `$` represents the end of a line. `\A` and `\Z` would represent the start and end of the buffer.

You are able to define general escape patterns to prevent escaped delimiters from being captured. Delimiter entries will have an opening, content (to allow a special pattern to represent inter-content escapes), and closing patterns. `closing` and `content` can see flags and groups specified in prior patterns like `open` etc. So if you set a case insensitive flag in the opening, it applies to content and closing as well.

The filter can be included via `pyspelling.filters.context`.

Options                 | Type     | Default       | Description
----------------------- | -------- | ------------- | -----------
`disallow`              | [string] | `#!py3 []`    | `SourceText` names to avoid processing.
`escapes`               | string   | `#!py3 ''`    | Regular expression pattern for character escapes outside delimiters.
`context_visible_first` | bool     | `#!py3 False` | Context will start as invisible and will be invisible between delimiters.
`delimiters`            | [dict]   | `#!py3 []`    | A list of dicts that define the regular expression delimiters.

```yaml
- name: python
  sources:
  - pyspelling
  filters:
  - pyspelling.filters.python:
      strings: false
      comments: false
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

To write a parser, there are two classes to be aware: `Filter` and `SourceText`. Both classes are found in `pyspelling.filters`.

When writing a filter, you'll often want to start by subclassing from the `Filter` class.  You'll often want to specify the default encoding and handle all of your custom options, and then pass the parameters to the base class.

```py3
from .. import filters


class HtmlFilter(filters.Filter):
    """Spelling Python."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        self.html_parser = HTMLParser()
        self.comments = options.get('comments', True) is True
        self.attributes = set(options.get('attributes', []))
        self.selectors = self.process_selectors(*options.get('ignores', []))
        super(HtmlFilter, self).__init__(options, default_encoding)
```

After that, there are four functions that are exposed for overrides. The fist is `header_check`. `header_check` receives the first 1024 characters of the file via `content` that can be scanned for an encoding header. A string with the encoding name should be returned or `None` if a valid encoding header cannot be found.

```py3
    def header_check(self, content):
        """Special encode check."""

        return None
```

`content_check` receives a file object which allows you to check the entire file buffer to determine encoding. A string with the encoding name should be returned or `None` if a valid encoding header cannot be found.

```py3
    def content_check(self, file_handle):
        """File content check."""

        return None
```

`filter` is called when the `Filter` object is the first in the chain. This means the file has not been read from disk yet, so we must handle opening the file before applying the filter and then return a list of `SourceText` objects. The first filter in the chain is handled differently in order to give the opportunity to handle files that initially must be parsed in binary format in order to extract the Unicode data. You can read the file in binary format or directly to Unicode.  You can run parsers or anything else you need to in order to get the Unicode text needed for the `SourceText` objects. You can create as many `SourceText` objects as you need and assign them categories so that other `Filter` objects can avoid them if desired. Below is the default which reads the entire file into a single object providing the file name as the context, the encoding, and the category `text`.

```py3
    def filter(self, source_file, encoding):  # noqa A001
        """Open and filter the file from disk."""

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            text = f.read()
        return [SourceText(text, source_file, encoding, 'text')]
```

`sfilter` is called for all `Filter` objects following the first.  The function is passed a `SourceText` object from which the text, context, encoding can all be extracted. Here you can manipulate the text back to bytes if needed, wrap the text in an `io.StreamIO` object to act as a file stream, run parsers, or anything you need to manipulate the buffer to filter the Unicode text for the `SourceText` objects.

```py3
    def sfilter(self, source):
        """Execute filter."""

        return [SourceText(source.text, source.context, source.encoding, 'text')]
```

If a filter only works either as the first in the chain, or only as a secondary filter in the chain, you could raise an exception if needed.  In most cases, you should be able to have an appropriate `filter` and `sfilter`, but there are most likely cases (particular when dealing with binary data) where only a `fitler` method could be provided.

Check check out the default filter plugins provided with the source to see real world examples.

And don't forget to provide a function in the file called `get_filter`! `get_filter` should return your `Filter` object.

```py3
def get_filter():
    """Return the filter."""

    return HtmlFilter
```

### Source Text Objects

As previously mentioned, filters must return a list of `SourceText` objects.

```py3
class SourceText(namedtuple('SourceText', ['text', 'context', 'encoding', 'category', 'error'])):
    """Source text."""

    __slots__ = ()

    def __new__(cls, text, context, encoding, category, error=None):
        """Allow defaults."""

        return super(SourceText, cls).__new__(cls, text, context, encoding, category, error)

    def _is_bytes(self):
        """Is bytes."""

        return isinstance(self.text, util.bstr)

    def _has_error(self):
        """Check if object has an error associated with it."""

        return self.error is not None
```

Each object should contain a Unicode string (`text`), some context on the given text hunk (`context`), the encoding which the Unicode text was originally in (`encoding`), and a `category` that is used to omit certain hunks from other filters in the chain (`category`). `SourceText` should not contain byte strings, and if they do, they will not be passed to additional filters.

Keep in mind when adjusting the context in subsequent items in the chain, you should really only append so as not to wipe out previous contextual data. It may not always make sense to append additional data, so some filters might just pass the previous context as the new context.

If you have a particular chunk of text that has a problem, you can return an error in the `SourceText` object.  Errors really only need a context and the error. `SourceText` objects with errors will not be passed down the chain and will not be passed to the spell checker.

```py3
        if error:
            content = [SourceText('', source_file, '', '', error)]
```
