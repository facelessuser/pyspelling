# URL

## Usage

This is a filter that simply strips URLs and/or email address from a file or text buffer. It takes an input buffer and
will return the buffer with URLs and/or emails addresses removed.

When first in the chain, the file's default, assumed encoding is `utf-8` unless otherwise overridden by the user.

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
