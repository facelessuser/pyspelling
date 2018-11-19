# Python

## Usage

When first in the chain, the Python filter will look for the encoding of the file in the header, and convert to Unicode accordingly. It will assume `utf-8` if no encoding header is found, and the user has not overridden the fallback encoding.

Text is returned in chunks based on the context of the captured text. Each docstrings, inline comment, or non-docstring is returned as their own chunk.

In general, regardless of Python version, strings *should* be parsed *almost* identically. PySpelling, unless configured otherwise, will decode string escapes and strip out format variables from f-strings. Decoding of escapes and stripping format variables is not dependent on what version of Python PySpelling is run on, but is based on the string prefixes that PySpelling encounters. There are two cases that may cause quirks related to Python version:

1. PySpelling doesn't support being run from Python 2, but it will still find strings and comments in Python 2 code as many Python 3 projects support Python 2 as well. If you run this on Python 2 code that is not using `#!py3 from __future__ import unicode_literals`, it will still treat the default strings in Python 2 code as Unicode as it has no way of knowing that a file is specifically meant for Python 2 parsing only. In general, you should use `unicode_literals` if you are supporting both Python 2 and 3.

2. Use of `\N{NAMED UNICODE}` *might* produce different results if one Python version defines a specific Unicode name while another does not. I'm not sure how greatly the named Unicode database varies from Python version to Python version, but if this is experienced, and is problematic, you can always disable `decode_escapes` in the options for a more consistent behavior.

```yaml
matrix:
- name: python
  pipeline:
  - pyspelling.filters.python:
      strings: false
      comments: false
  sources:
  - pyspelling/**/*.py
```

## Filtering String types

When `strings` is enabled, you can specify which strings you want to allow via the `string_types` option. Valid string types are `b` for bytes, `f` for format, `u` for Unicode (all variants), and `R` for raw.  `f` refers to f-strings, not strings in the form `#!py3 "my string {}".format(value)"`. Case is not important, and the default value is `fu`.

If you do not explicitly specify `b`, `u` is assumed. For instance, if only `r` was specified, there is actually multiple types of `r`: bytes and Unicode. Since bytes was not explicitly specified, `u` is assumed to be enabled and both `u` and `u` variants of `r` will be searched. If you specified `br`, you would be searching `b` strings and `b` variants of `r` and not `u` strings. To search both `u` and `b` strings you would need to specify `ubr`.

In short, if you enable `f` or `r`, you will be searching the normal string of that type as well as `f` and `r` types are subtypes of of `u` and `b` (`f` does not have `b` variants). If greater resolution is needed, this approach may be reconsidered in the future.

## Options

Options          | Type     | Default       | Description
---------------- | -------- | ------------- | -----------
`comments`       | bool     | `#!py3 True`  | Return `SourceText` entries for each comment.
`docstrings`     | bool     | `#!py3 True`  | Return `SourceText` entries for each docstrings.
`group_comments` | bool     | `#!py3 False` | Group consecutive Python comments as one `SourceText` entry.
`decode_escapes` | bool     | `#!py3 True`  | Decode escapes and strip out format variables. Behavior is based on the string type that is encountered. This affects both docstrings and non-docstrings.
`strings`        | string   | `#!py3 False` | Return `SourceText` entries for each string (non-docstring).
`strint_types`   | string   | `#!py3 fu`    | Specifies which string types `strings` searches: bytes (`b`), format (`f`), raw (`r`), and Unicode (`u`). This does not affect docstrings. When `docstrings` is enabled, all docstrings are parsed.

## Categories

Python returns text with the following categories.

Category       | Description
-------------- | -----------
`py-comments`  | Text captured from inline comments.
`py-docstring` | Text captured from docstrings.
`py-string`    | Text captured from strings.
