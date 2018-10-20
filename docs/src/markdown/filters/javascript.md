# JavaScript

When first int the chain, the JavaScript filter uses no special encoding detection. It will assume `utf-8` if no encoding BOM is found, and the user has not overridden the fallback encoding. Text is returned in blocks based on the context of the text depending on what is enabled.  The parser can return JSDoc comments, block comments, and/or inline comments. Each is returned as its own object.

Options          | Type     | Default       | Description
---------------- | -------- | ------------- | -----------
`disallow`       | [string] | `#!py3 []`    | `SourceText` names to avoid processing.
`block_comments` | bool     | `#!py3 True`  | Return `SourceText` entries for each block comment.
`line_comments`  | bool     | `#!py3 True`  | Return `SourceText` entries for each line comment.
`jsdocs`         | bool     | `#!py3 False` | Return `SourceText` entries for each JSDoc comment.
`group_comments` | bool     | `#!py3 False` | Group consecutive Python comments as one `SourceText` entry.

```yaml
- name: javascript
  filters:
  - pyspelling.filters.javascript
      jsdocs: true
      line_comments: false
      block_comments: false
  sources:
  - js_files/**/*.js
```
