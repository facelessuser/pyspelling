# Filters

## Overview

Filters are chainable PySpelling plugins that filter the content of a buffer and return only the portions that are desired. The portions that are returned are partitioned in to chunks that contain a little contextual information. Some filters may return only one chunk in the list that is the entirety of the file, and some may return context specific chunks: one for each docstring, one for each comment, etc. The metadata associated with each chunk can be used to halt filtering of specific chunks in the chain. Some of the metadata is also used to give feedback to the user when results are displayed.

Each chunk returned by the filter is a `SourceText` object. These objects contain the desired, filtered text from the source along with some metadata: encoding, display context, and a category that describes what kind of text the data is. After all filters have processed the text, each `SourceText` text is finally passed to Aspell.

The text data in a `SourceText` object is always Unicode, but during the filtering process, the filter can decode the Unicode if required as long as it is returned as Unicode at the end. The first filter in the chain is always responsible for initially reading the file from disk and getting the file content into a Unicode buffer that PySpelling can work with. It is also responsible for identifying encoding from the file header if there is special logic to determine such things.

## Available Filters

PySpelling comes with a couple of built-in filters.

### Text

This is a filter that simply retrieves the buffer's text and returns it as Unicode.  It takes a file or file buffer and returns a single `SourceText` object containing all the text in the file.  It is the default is no filter is specified and can be manually included via `pyspelling.filters.text`. When first in the chain, the file's default, assumed encoding of the is `ascii` unless otherwise overridden by the user.

Options               | Type          | Default    | Description
--------------------- | ------------- | ---------- | -----------
`disallow`            | [string]      | `#!py3 []` | `SourceText` names to avoid processing.

### Markdown

The Markdown filter converts a text file's buffer using Python Markdown and returns a single `SourceText` object containing the text as HTML. It can be included via `pyspelling.filters.markdown`. When first in the chain, the file's default, assumed encoding of the is `utf-8` unless otherwise overridden by the user.

Options               | Type          | Default    | Description
--------------------- | ------------- | ---------- | -----------
`disallow`            | [string]      | `#!py3 []` | `SourceText` names to avoid processing.
`markdown_extensions` | [string/dict] | `#!py3 []` | A list of strings defining markdown extensions to use. You can substitute the string with a dict that defines the extension as the key and the value as a dictionary of options.

```yaml
- name: Markdown
  filters:
    - pyspelling.parsers.markdown_parser
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
    - pyspelling.filters.html
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
    - pyspelling.filters.python
        options:
          strings: false
          comments: false
  sources:
  - pyspelling/**/*.py
```

### JavaScript

When first int the chain, the JavaScript filter uses no special encoding detection. It will assume `ascii` if no encoding BOM is found, and the user has not overridden the fallback encoding. Text is returned in blocks based on the context of the text depending on what is enabled.  The parser can return JSDoc comments, block comments, and/or inline comments. Each is returned as its own object.

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

### Writing a Parser

To write a parser, there are three classes to be aware: `Decoder`, `Filter`, and `SourceText` which are all found in `pyspelling.filters`. In general, you'll only need to define your own `Decoder` class if you have special considerations in regard to encoding, such as a header deceleration that defines decoding.

If you need a `Decoder`, there are two functions that you can override: `header_check` and `content_check`. `header_check` receives the first 1024 characters of the file so you can check for a header declaration, while `content_check` receives the file handle so you can do what you need to. Both should return either the encoding or `None` if an encoding could not be determined.

The HTML decoder as a simplified example:

```py3
class HTMLDecoder(parsers.Decoder):
    """Detect HTML encoding."""

    def header_check(self, content):
        """Special HTML encoding check."""

        encode = None
        m = RE_HTML_ENCODE.search(content)
        if m:
            encode = m.group(1).decode('ascii')
        return encode
```

`Filter` is the class you will always need to provide. There are two functions you will want to override: `__init__` which handles your options and `filter` which handles the "first in the chain" file handling (opening, decoding, and initial filtering), and `sfilter` which filters a string buffer. There is also one attribute you may want to define as well: `DECODER` which you'd set to your custom `Decoder` if you have one.

So below we have the HTML parser that uses the `Decoder` we defined earlier.  You'll notice that we are leveraging the HTML filter for the parser.

```py3
class HtmlFilter(filters.Filter):
    """Spelling Python."""

    DECODER = HTMLDecoder

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        self.html_parser = HTMLParser()
        self.comments = options.get('comments', True) is True
        self.attributes = set(options.get('attributes', []))
        self.selectors = self.process_selectors(*options.get('ignores', []))
        super(HtmlFilter, self).__init__(options, default_encoding)

    def html_to_text(text):
        """Extract the text from the HTML objects."""

        # Do some work

        return text

    def _filter(self, text):
        """Filter the source text."""

        return self.html_to_text(bs4.BeautifulSoup(text, "html5lib"))

    def filter(self, source_file, encoding):
        """Parse HTML file."""

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            text = f.read()
        return [filters.SourceText(self._filter(text), source_file, encoding, 'html')]

    def sfilter(self, source):
        """Filter."""

        return [filters.SourceText(self._filter(source.text), source.context, source.encoding, 'html')]
```

Lastly, the parser must return a list of `SourceText` objects.  Each object should contain a Unicode string. `SourceText` objects with byte strings will not be passed to additional filters.  The object needs to return some metadata giving context which can simply be the source file name as shown above, or it can contain more info such a line number of the block of text etc. The encoding of the text should also be returned along with a category that describes the type of text. The identifier is used to exclude certain `SourceText` objects from filters later on.

Keep in mind when adjusting the context, you should really only append as not to wipe out previous contextual data. Aside from the first in chain case, additional filters are not required to modify the context unless more useful context can be added.  In the case above, since the the HTML filter augments the data so much, things like line numbers would not really be helpful anymore, so `sfilter` just uses the existing context, while `filter` (first in the chain filter) just sets the file name.

If you have a particular chunk of text that has a problem, you can return an error.  Errors really only need a valid meta data entry and the error.

```py3
        if error:
            content = [SourceText('', source_file, '', '', error)]
```

Don't forget to provide a function called `get_filter` to return your parser:

```py3
def get_filter():
    """Return the filter."""

    return HtmlFilter
```
