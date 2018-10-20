# JavaScript

## Usage

When first in the chain, the JavaScript filter uses no special encoding detection. It will assume `utf-8` if no encoding BOM is found, and the user has not overridden the fallback encoding. Text is returned in chunks based on the context of the text.  The filter can return JSDoc comments, block comments, and/or inline comments.

```yaml
matrix:
- name: javascript
  pipeline:
  - pyspelling.filters.javascript
      jsdocs: true
      line_comments: false
      block_comments: false
  sources:
  - js_files/**/*.js
```

## Options

Options          | Type     | Default       | Description
---------------- | -------- | ------------- | -----------
`block_comments` | bool     | `#!py3 True`  | Return `SourceText` entries for each block comment.
`line_comments`  | bool     | `#!py3 True`  | Return `SourceText` entries for each line comment.
`jsdocs`         | bool     | `#!py3 False` | Return `SourceText` entries for each JSDoc comment.
`group_comments` | bool     | `#!py3 False` | Group consecutive Python comments as one `SourceText` entry.

## Categories

JavaScript returns text with the following categories.

Category           | Description
------------------ | -----------
`js-block-comment` | Text captured from JavaScript block comments.
`js-line-comment`  | Text captured from JavaScript line comments.
`js-docs`          | Text captured from JSDoc comments.
