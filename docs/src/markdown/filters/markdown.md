# Markdown

## Usage

The Markdown filter converts a text file's buffer using Python Markdown and returns a single `SourceText` object
containing the text as HTML. It can be included via `pyspelling.filters.markdown`. When first in the chain, the file's
default, assumed encoding is `utf-8` unless otherwise overridden by the user.

/// tip
The Markdown filter is not always needed. While Aspell has a built-in Markdown mode, it can be somewhat limited in
ignoring content for advanced cases, but if all you need is basic Markdown support, then you can often just use Aspell's
Markdown mode.

```yaml
- name: markdown
  group: docs
  sources:
  - README.md
  - INSTALL.md
  - LICENSE.md
  - CODE_OF_CONDUCT.md
  aspell:
    lang: en
    d: en_US
    mode: markdown
  dictionary:
    wordlists:
    - .spell-dict
    output: build/dictionary/markdown.dic
```

PySpelling's Markdown filter is useful if you:

-   Already use Python Markdown and it's custom extensions and need support for the custom extensions.
-   Need to convert the content to HTML to use PySpelling's advanced HTML filter to ignore content with CSS selectors.

Python Markdown is not a CommonMark parser either, so if you need such a parser, you may have find and/or write your
own.
///

To configure the Python Markdown filter, you can include it in the pipeline and setup various Markdown extensions if
desired.

```yaml
matrix:
- name: markdown
  pipeline:
  - pyspelling.filters.markdown:
      markdown_extensions:
      - markdown.extensions.toc:
          slugify: !!python/name:pymdownx.slugs.uslugify
          permalink: "\ue157"
      - markdown.extensions.admonition
      - markdown.extensions.smarty
  source:
  - **/*.md
```

## Options

Options               | Type          | Default    | Description
--------------------- | ------------- | ---------- | -----------
`markdown_extensions` | [string/dict] | `#!py3 []` | A list of strings defining markdown extensions to use. You can substitute the string with a dict that defines the extension as the key and the value as a dictionary of options.

## Categories

Markdown returns text with the following categories.

Category   | Description
---------- | -----------
`markdown` | Text rendered in HTML.
