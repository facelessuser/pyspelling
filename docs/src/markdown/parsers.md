# Parsers

## Overview

Parsers are PySpelling plugins that take care of properly detecting an encoding (if applicable) and parsing the file into a list of relevant text chunks. Some parsers may return only one entry in the list that is the entirety of the file, and some may return context specific chunks: one for each docstring, one for each comment etc.

In general, parsers will detect the encoding of the file, and return one or more `SourceText` objects.  These objects contain the snippets of text from the file with some meta data with things like encoding etc. Later in the process, the content of these objects are fed through PySpelling filters, and finally passed to Aspell. If the text within a `SourceText` object is not Unicode, filters will be skipped for that instance.

## Available Parsers

PySpelling comes with a couple of built-in parsers.

### Raw

The Raw parser will not bother to detect encoding, and will instead only use the `default_encoding` provided by the user. It will return the content a byte string in a single `SourceText` object that will be passed directly to Aspell bypassing additional filters. It is included via `pyspelling.parsers.raw_parser`.

### Text

This is a parser that parsers general text files to Unicode.  It takes a file and returns a single `SourceText` object containing the content of the file.  It can be included via `pyspelling.parsers.text_parser`.

### Markdown

The Markdown parser converts a text file using Python Markdown and returns a single `SourceText` object containing HTML text. It can be included via `pyspelling.parsers.markdown_parser`.

### HTML

The HTML parsers will look for the encoding of the HTML in its header and convert the buffer to Unicode.  It then uses BeautifulSoup4 to convert the content to HTML, and then aggregates all text that should be spell checked in a single `SourceText` object.  It can be configured to avoid certain tags, classes, IDs, or other attributes if desired.  It can also be instructed to scan certain tag attributes for content to spell check. It can be included via `pyspelling.parsers.html_parser`.

### Python

The Python parser will look for the encoding of the file in the header, and convert to Unicode accordingly. If no encoding is specified, the encoding is assumed to be ASCII. User specified default encoding will be ignored.

Text is returned in blocks based on the context of the text.  Each docstring is returned as its own object.  Comments are returned as their own as well as strings. This is in case you do something like write your docstrings in Markdown, you can run each one individually through the Markdown filter, or some other filter if required.

### Writing a Parser

Under construction.
