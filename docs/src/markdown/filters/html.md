# HTML

When first in the chain, the HTML filter will look for the encoding of the HTML in its header and convert the buffer to Unicode. It will assume `utf-8` if no encoding header is found, and the user has not overridden the fallback encoding.

The HTML filter uses BeautifulSoup4 to convert the Unicode content to HTML, and then aggregates all text that should be spell checked in a single `SourceText` object.  It can be configured to avoid certain tags, classes, IDs, or other attributes if desired.  It can also be instructed to scan certain tag attributes for content to spell check. It can be included via `pyspelling.parsers.html_parser`.

Options      | Type     | Default      | Description
------------ | -------- | ------------ | -----------
`disallow`   | [string] | `#!py3 []`   | `SourceText` names to avoid processing.
`comments`   | bool     | `#!py3 True` | Include comment text in the output.
`attributes` | [string] | `#!py3 []`   | Attributes whose content should be included in the output.
`ignores`    | [string] | `#!py3 []`   | Simple selectors that identify tags to ignore. Only allows tags, IDs, classes, and other attributes.

```yaml
- name: mkdocs
  filters:
  - pyspelling.filters.html:
      comments: false
      attributes:
      - title
      - alt
      ignores:
      - code
      - pre
      - a.magiclink-compare
      - a.magiclink-commit
      - span.keys
      - .MathJax_Preview
      - .md-nav__link
      - .md-footer-custom-text
      - .md-source__repository
      - .headerlink
      - .md-icon
  sources:
  - site/*.html
```
