# Python

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
