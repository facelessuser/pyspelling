# CPP

## Usage

The CPP plugin is designed to find and return C/C++ style comments. When first in the chain, the CPP filter uses no special encoding detection. It will assume `utf-8` if no encoding BOM is found, and the user has not overridden the fallback encoding. Text is returned in chunks based on the context of the text: block or inline.

As C++ style comments are fairly common convention in other languages, this can often be used for other syntaxes. The JavaScript and Stylesheets plugin are actually derived from this one. If using this for another syntax language, you can actually augment the returned categories by providing an alternative prefix to via the options.  The default is `cpp`.

```yaml
matrix:
- name: cpp
  pipeline:
  - pyspelling.filters.cpp
      line_comments: false
  sources:
  - js_files/**/*.{cpp,hpp,c,h}
```

## Options

Options          | Type     | Default       | Description
---------------- | -------- | ------------- | -----------
`block_comments` | bool     | `#!py3 True`  | Return `SourceText` entries for each block comment.
`line_comments`  | bool     | `#!py3 True`  | Return `SourceText` entries for each line comment.
`group_comments` | bool     | `#!py3 False` | Group consecutive inline comments as one `SourceText` entry.

## Categories

JavaScript returns text with the following categories.

Category            | Description
------------------- | -----------
`cpp-block-comment` | Text captured from C++ style block comments.
`cpp-line-comment`  | Text captured from C++ style line comments.
