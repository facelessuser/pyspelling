# Python

## Usage

When first in the chain, the Python filter will look for the encoding of the file in the header, and convert to Unicode accordingly. It will assume `utf-8` if no encoding header is found, and the user has not overridden the fallback encoding.

Text is returned in chunks based on the context of the captured text. Each docstrings and inline comments is returned as their own chunk.

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

## Options

Options          | Type     | Default       | Description
---------------- | -------- | ------------- | -----------
`comments`       | bool     | `#!py3 True`  | Return `SourceText` entries for each comment.
`docstrings`     | bool     | `#!py3 True`  | Return `SourceText` entries for each docstrings.
`group_comments` | bool     | `#!py3 False` | Group consecutive Python comments as one `SourceText` entry.
`strings`        | string   | `#!py3 False` | Return `SourceText` entries for each string (non-docstring).
`allowed`        | string   | `#!py3 fu`    | Specifies which string types `strings` searches: bytes (`b`), format (`f`), raw (`r`), and Unicode (`u`). 

## Categories

Python returns text with the following categories.

Category       | Description
-------------- | -----------
`py-comments`  | Text captured from inline comments.
`py-docstring` | Text captured from docstrings.
`py-string`    | Text captured from strings.
