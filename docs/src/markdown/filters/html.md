# HTML

## Usage

The HTML filter is designed to capture HTML content, comments, and even attributes. It allows for filtering out specific
tags, and you can even filter them out with basic selectors.

When first in the chain, the HTML filter will look for the encoding of the HTML in its header and convert the buffer to
Unicode. It will assume `utf-8` if no encoding header is found, and the user has not overridden the fallback encoding.

The HTML filter uses BeautifulSoup4 to convert the Unicode content to HTML. Content is returned in individual chunks by
block tags. While this causes more overhead, as each block is processed individually through the command line tool, it
provides context for where the spelling errors are. If enabled, the HTML filter will also return chunks for comments and
even attributes. Each type of text chunk is returned with their own category type.

Tags can be captured or ignored with the `captures` and `ignores` options. These options work by employing CSS selectors
to target the tags. The CSS selectors are based on a limited subset of CSS4 selectors.

```yaml
matrix:
- name: html
  pipeline:
  - pyspelling.filters.html:
      comments: false
      attributes:
      - title
      - alt
      ignores:
      - :matches(code, pre)
      - a:matches(.magiclink-compare, .magiclink-commit)
      - span.keys
      - :matches(.MathJax_Preview, .md-nav__link, .md-footer-custom-text, .md-source__repository, .headerlink, .md-icon)
  sources:
  - site/*.html
```

## Supported CSS Selectors

The CSS selectors are based on a limited subset of CSS4 selectors. Support is provided via Soup Sieve. Please reference
[Soup Sieve's documentation][soup-sieve] for more info.

## Options

Options      | Type     | Default                           | Description
------------ | -------- | --------------------------------- | -----------
`comments`   | bool     | `#!py3 True`                      | Include comment text in the output.
`attributes` | [string] | `#!py3 []`                        | Attributes whose content should be included in the output.
`ignores`    | [string] | `#!py3 []`                        | CSS style selectors that identify tags to ignore. Child tags will not be crawled.
`captures`   | [string] | `#!py3 ['*|*:not(script,style)']` | CSS style selectors used to narrow which tags that text is collected from. Unlike `ignores`, tags which text is not captured from still have their children crawled.
`mode`       | string   | `#!py3 'html`                     | Mode to use when parsing HTML: `html`, `xhtml`, `html5`.
`namespaces` | dict     | `#!py3 {}`                        | Dictionary containing key value pairs of namespaces to use for CSS selectors (equivalent to `@namespace` in CSS). Use the an empty string for the key to define default the namespace. See below for example.
`break_tags` | [string] | `#!py3 []`                        | Additional tags (in addition to the default, defined block tags), to break on for context. Useful for new or currently unsupported block tags.

!!! example "Namespace example"
    ```yaml
    matrix:
    - name: html
      pipeline:
      - pyspelling.filters.html:
          mode: xhtml
          namespaces:
            "": http://www.w3.org/1999/xhtml
            svg: http://www.w3.org/2000/svg
            xlink: http://www.w3.org/1999/xlink
    ```

## Categories

HTML returns text with the following categories.

Category         | Description
---------------- | -----------
`html-content`   | Text captured from HTML blocks.
`html-attribute` | Text captured from HTML attributes.
`html-comment`   | Text captured from HTML comments.

--8<--
refs.txt
--8<--
