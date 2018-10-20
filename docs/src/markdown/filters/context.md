# Context

The Context filter is used to create regular expression context delimiters for filtering content you want and don't want. Delimiters are defined in pairs, and depending on how the filter is configured, the opening delimiter will swap from ignoring text to gathering text. And when the closing delimiter is met, the filter will swap back from gathering text to ignoring text.  If `context_visible_first` is set to `true`, the logic will be reversed.

Regular expressions are compiled with the MULTILINE flag so that `^` represents the start of a line and `$` represents the end of a line. `\A` and `\Z` would represent the start and end of the buffer.

You are able to define general escape patterns to prevent escaped delimiters from being captured. Delimiter entries will have an opening, content (to allow a special pattern to represent inter-content escapes), and closing patterns. `closing` and `content` can see flags and groups specified in prior patterns like `open` etc. So if you set a case insensitive flag in the opening, it applies to content and closing as well.

The filter can be included via `pyspelling.filters.context`.

Options                 | Type     | Default       | Description
----------------------- | -------- | ------------- | -----------
`disallow`              | [string] | `#!py3 []`    | `SourceText` names to avoid processing.
`escapes`               | string   | `#!py3 ''`    | Regular expression pattern for character escapes outside delimiters.
`context_visible_first` | bool     | `#!py3 False` | Context will start as invisible and will be invisible between delimiters.
`delimiters`            | [dict]   | `#!py3 []`    | A list of dicts that define the regular expression delimiters.

```yaml
- name: python
  sources:
  - pyspelling
  filters:
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
