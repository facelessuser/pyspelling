# URL

## Usage

This is a filter that simply strips URLs and/or email address from a file or text buffer.  It takes a file or file buffer and returns a single `SourceText` object containing all the text in the file without URLs or email addresses.  When first in the chain, the file's default, assumed encoding is `utf-8` unless otherwise overridden by the user.

```yaml
matrix:
- name: url
  pipeline:
  - pyspelling.filters.url:
  source:
  - "**/*.txt"
```

## Options

Options  | Type | Default      | Description
-------- | ---- | ------------ | -----------
`urls`   | bool | `#!py3 True` | Enables or disables URL stripping.
`emails` | bool | `#!py3 True` | Enables or disables email address stripping.

## Categories

Text returns text with the following categories.

Category   | Description
---------- | -----------
`url-free` | The text without URLs and/or emails.
