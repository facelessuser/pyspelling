# Stylesheets

## Usage

The Stylesheets plugin is designed to find and return comments in CSS, SCSS, and SASS (CSS does not support inline comments). When first in the chain, the filter uses no special encoding detection. It will assume `utf-8` if no encoding BOM is found, and the user has not overridden the fallback encoding. Text is returned in chunks based on the context of the text: block or inline.

You can specify `sass` or `scss` in the option `stylesheets` if you need to capture inline comments.

```yaml
matrix:
- name: scss
  pipeline:
  - pyspelling.filters.stylesheets:
      stylesheets: scss
  default_encoding: utf-8
  sources:
  - docs/src/scss/*.scss
  aspell:
    lang: en
  dictionary:
    lang: en
    wordlists:
    - docs/src/dictionary/en-custom.txt
    output: build/dictionary/scss.dic
```

## Options

Options          | Type     | Default       | Description
---------------- | -------- | ------------- | -----------
`stylesheets`    | string   | `#!py3 "css"` | The stylesheet mode.
`block_comments` | bool     | `#!py3 True`  | Return `SourceText` entries for each block comment.
`line_comments`  | bool     | `#!py3 True`  | Return `SourceText` entries for each line comment.
`group_comments` | bool     | `#!py3 False` | Group consecutive inline comments as one `SourceText` entry.

## Categories

Stylesheets returns text with the following categories depending on what stylesheet mode is enabled. Categories prefixed with `css` are for CSS etc.

Category             | Description
-------------------- | -----------
`css-block-comment`  | Text captured from CSS block comments.
`scss-block-comment` | Text captured from SCSS block comments.
`scss-line-comment`  | Text captured from SCSS line comments.
`sass-block-comment` | Text captured from SASS block comments.
`sass-line-comment`  | Text captured from SASS line comments.
