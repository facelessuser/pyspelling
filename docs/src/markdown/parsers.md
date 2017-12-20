# Parsers

## Overview

Parsers are PySpelling plugins that take care of properly detecting an encoding (if applicable) and parsing the file into a list of relevant text chunks. Some parsers may return only one entry in the list that is the entirety of the file, and some may return context specific chunks: one for each docstring, one for each comment etc.

In general, parsers will detect the encoding of the file, and return one or more `SourceText` objects.  These objects contain the snippets of text from the file with some meta data with things like encoding etc. Later in the process, the content of these objects are fed through PySpelling filters, and finally passed to Aspell. If the text within a `SourceText` object is not Unicode, filters will be skipped for that instance.

## Available Parsers

PySpelling comes with a couple of built-in parsers.

### Raw

The Raw parser will not bother to detect encoding, it will return the content as a byte string in a single `SourceText` object with the `default_encoding` provided by the user, all of which will be passed directly to Aspell bypassing additional filters. It is included via `pyspelling.parsers.raw_parser`.

### Text

This is a parser that parsers general text files to Unicode.  It takes a file and returns a single `SourceText` object containing the content of the file.  It can be included via `pyspelling.parsers.text_parser`.

### Markdown

The Markdown parser converts a text file using Python Markdown and returns a single `SourceText` object containing HTML text. It can be included via `pyspelling.parsers.markdown_parser`.

Options               | Type          | Default    | Description
--------------------- | ------------- | ---------- | -----------
`markdown_extensions` | [string/dict] | `#!py3 []` | A list of strings defining markdown extensions to use. You can substitute the string with a dict that defines the extension as the key and the value as a dictionary of options.

```yaml
- name: Markdown
  parser: pyspelling.parsers.markdown_parser
  options:
    markdown_extensions:
    - markdown.extensions.toc:
        slugify: !!python/name:pymdownx.slugs.uslugify
        permalink: "\ue157"
    - markdown.extensions.admonition
    - markdown.extensions.smarty
  default_encoding: utf-8
```

### HTML

The HTML parsers will look for the encoding of the HTML in its header and convert the buffer to Unicode.  It then uses BeautifulSoup4 to convert the content to HTML, and then aggregates all text that should be spell checked in a single `SourceText` object.  It can be configured to avoid certain tags, classes, IDs, or other attributes if desired.  It can also be instructed to scan certain tag attributes for content to spell check. It can be included via `pyspelling.parsers.html_parser`.

Options      | Type     | Default      | Description
------------ | -------- | ------------ | -----------
`comments`   | bool     | `#!py3 True` | Include comment text in the output.
`attributes` | [string] | `#!py3 []`   | Attributes whose content should be included in the output.
`ignores`    | [string] | `#!py3 []`   | Simple selectors that identify tags to ignore. Only allows tags, IDs, classes, and other attributes.

```yaml
- name: mkdocs
  parser: pyspelling.parsers.html_parser
  options:
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
  - site
```

### Python

The Python parser will look for the encoding of the file in the header, and convert to Unicode accordingly. If no encoding is specified, the encoding is assumed to be ASCII. User specified default encoding will be ignored.

Text is returned in blocks based on the context of the text.  Each docstring is returned as its own object.  Comments are returned as their own as well as strings. This is in case you do something like write your docstrings in Markdown, you can run each one individually through the Markdown filter, or some other filter if required.

Options          | Type | Default       | Description
---------------- | ---- | ------------- | -----------
`comments`       | bool | `#!py3 True`  | Return `SourceText` entries for each comment.
`docstrings`     | bool | `#!py3 True`  | Return `SourceText` entries for each docstrings.
`strings`        | bool | `#!py3 False` | Return `SourceText` entries for each string.
`bytes`          | bool | `#!py3 False` | Return `SourceText` entries for each byte string. Only ASCII content will be included, and encoding will be returned as ASCII.
`group_comments` | bool | `#!py3 False` | Group consecutive Python comments as one `SourceText` entry.

```yaml
- name: python
  parser: pyspelling.parsers.python_parser
  options:
    strings: false
    comments: false
  sources:
  - pyspelling
```

### Writing a Parser

To write a parser, there are three classes to be aware: `Decoder`, `Parser`, and `SourceText` which are all found in `pyspelling.parsers`. In general, you'll only need to define your own `Decoder` class if you have special considerations in regard to encoding, such as a header deceleration that defines decoding.

If you need a `Decoder`, there are two functions that you can override: `header_check` and `content_check`. `header_check` receives the first 1024 characters of the file so you can check for a header declaration, while `content_check` receives the file handle so you can do what you need to. Both should return either the encoding or `None` if an encoding could not be determined.

The HTML decoder as an example:

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

The Parser is the class you will always need to provide. There are two functions you will want to override: `__init__` which handles your options and `parse_file` which does the actual work. There are also two attributes you may want to define as well: `EXTENSIONS` which defines the accepted file patterns and `DECODER` which you'd set to your custom `Decoder` if you have one.

So below we have the HTML parser that uses the `Decoder` we defined earlier.  You'll notice that we are leveraging the HTML filter for the parser.

```py3
class HTMLParser(parsers.Parser):
    """Spelling Python."""

    FILE_PATTERNS = ('*.html', '*.htm')
    DECODER = HTMLDecoder

    def __init__(self, options, default_encoding='ascii'):
        """Initialization."""

        self.filter = html_filter.HTMLFilter(options)
        super(HTMLParser, self).__init__(options, default_encoding)

    def parse_file(self, source_file, encoding):
        """Parse HTML file."""

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            text = f.read()
        content = [parsers.SourceText(self.filter.filter(text, encoding), source_file, encoding, 'html')]

        return content
```

Lastly, the parser must return a list of `SourceText` objects.  Each object should contain a Unicode or bytes string. `SourceText` objects with byte strings will not be passed to additional filters.  The object needs to return some meta data describing the content which can simply be the source file name as shown above, or it can contain more info such a line number of the block of text etc. The encoding of the text should also be returned along with an identifier for type of text. The identifier is used to exclude certain `SourceText` objects from filters later on.

If you have a particular chunk of text that has a problem, you can return an error.  Errors really only need a valid meta data entry and the error.

```py3
        if error:
            content = [SourceText('', source_file, '', '', error)]
```

Don't forget to provide a function called `get_parser` to return your parser:

```py3
def get_parser():
    """Return the parser."""

    return HTMLParser
```
