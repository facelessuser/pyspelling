# Context

## Usage

The Context filter is used to create regular expression context delimiters for filtering out content you want from content you don't want. Depending on how the filter is configured, the opening delimiter will swap from ignoring text to gathering text. When the closing delimiter is met, the filter will swap back from gathering text to ignoring text.  If `context_visible_first` is set to `true`, the logic will be reversed.

Regular expressions are compiled with the MULTILINE flag so that `^` represents the start of a line and `$` represents the end of a line. `\A` and `\Z` would represent the start and end of the buffer.

Delimiters require an `open` and a `close` pattern. You can optionally define a `content` pattern, but if you don't, it is `.*?` by default. The three patterns are used to create a single regular expression in the form `#!py3 r'{0}(?P<special_group_name>{1})(?:{2}|\Z)'`, where `{0}` is the opening pattern is inserted, `{1}` is the content pattern , and `{2}` is the closing pattern. `special_group_name` is randomly generated to ensure it doesn't conflict with anything in the pattern. Keeping in mind that these are all compiled into one pattern, you are able to define capture group names in opening, and reference them in the closing if needed.

You can also able to define a global escape pattern to prevent escaped delimiters from being captured.

The filter can be included via `pyspelling.filters.context`.

```yaml
matrix:
- name: python
  sources:
  - pyspelling
  pipeline:
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

## Options

Options                 | Type     | Default       | Description
----------------------- | -------- | ------------- | -----------
`escapes`               | string   | `#!py3 ''`    | Regular expression pattern for character escapes outside delimiters.
`context_visible_first` | bool     | `#!py3 False` | Context will start as invisible and will be invisible between delimiters.
`delimiters`            | [dict]   | `#!py3 []`    | A list of dicts that define the regular expression delimiters.

## Categories

Context returns text with the following categories.

Category  | Description
--------- | -----------
`context` | Text captured by the via context.
