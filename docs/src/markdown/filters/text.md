# Text

## Usage

This is a filter that simply retrieves the buffer's text and returns it as Unicode.  It takes a file or file buffer and returns a single `SourceText` object containing all the text in the file.  It is the default filter when there is no filter specified, though it can be manually included via `pyspelling.filters.text`. When first in the chain, the file's default, assumed encoding is `utf-8` unless otherwise overridden by the user.

The Text filter can also be used convert from one encoding to another.

```yaml
matrix:
- name: text
  default_encoding: cp1252
  pipeline:
  - pyspelling.filters.text:
      convert_encoding: utf-8
  source:
  - "**/*.txt"
```

## Options

Options               | Type          | Default          | Description
--------------------- | ------------- | ---------------- | -----------
`normalize`           | string        | `#!py3 ''`       | Performs Unicode normalization. Valid values are `NFC`, `NFD`, `NFKC`, and `NFKD`.
`convert_encoding`    | string        | `#!py3 ''`       | Assuming a valid encoding, the text will be converted to the specified encoding.
`errors`              | string        | `#!py3 'strict'` | Specifies what to do when converting the encoding, and a character can't be converted. Valid values are `strict`, `ignore`, `replace`, `xmlcharrefreplace`, `backslashreplace`, and `namereplace`.

## Categories

Text returns text with the following categories.

Category   | Description
---------- | -----------
`text`     | The extracted text.
