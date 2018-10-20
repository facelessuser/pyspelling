# Markdown

The Markdown filter converts a text file's buffer using Python Markdown and returns a single `SourceText` object containing the text as HTML. It can be included via `pyspelling.filters.markdown`. When first in the chain, the file's default, assumed encoding is `utf-8` unless otherwise overridden by the user.

Options               | Type          | Default    | Description
--------------------- | ------------- | ---------- | -----------
`disallow`            | [string]      | `#!py3 []` | `SourceText` names to avoid processing.
`markdown_extensions` | [string/dict] | `#!py3 []` | A list of strings defining markdown extensions to use. You can substitute the string with a dict that defines the extension as the key and the value as a dictionary of options.

```yaml
- name: Markdown
  filters:
  - pyspelling.parsers.markdown_parser:
      markdown_extensions:
      - markdown.extensions.toc:
          slugify: !!python/name:pymdownx.slugs.uslugify
          permalink: "\ue157"
      - markdown.extensions.admonition
      - markdown.extensions.smarty
  source:
  - **/*.md
```
