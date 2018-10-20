# HTML

## Usage
The HTML filter is designed to capture HTML content, comments, and even attributes. It allows for filtering out specific tags, and you can even filter them out with basic selectors.

When first in the chain, the HTML filter will look for the encoding of the HTML in its header and convert the buffer to Unicode. It will assume `utf-8` if no encoding header is found, and the user has not overridden the fallback encoding.

The HTML filter uses BeautifulSoup4 to convert the Unicode content to HTML. Content is returned in individual chunks by block tags. If enabled the HTML filter will also return chunks for comments and even attributes. Each type of text chunk is returned with their own category type.

Tags can be ignored with basic CSS selectors.

Selector             | Example               | Description
-------------------- | --------------------- | -----------
`Element`            | `div`                 | Select the `<div>` element.
`.class`             | `.some-class`         | Select all elements with the class `some-class`.
`#id`                | `#some-id`            | Select the element with the ID `some-id`.
`*`                  | `*`                   | Select all elements.
`[attribute]`        | `[target]`            | Selects all elements with a `target` attribute.
`[attribute=value]`  | `[target=_blank]`     | Selects all elements with `target="_blank"`.
`[attribute~=value]` | `[title~=flower]`     | Selects all elements with a title attribute containing the word `flower`.
`[attribute|=value]` | `[lang|=en]`          | Selects all elements with a `lang` attribute value starting with `en`.
`[attribute^=value]` | `a[href^="https"]`    | Selects every `<a>` element whose `href` attribute value begins with `https`.
`[attribute$=value]` | `a[href$=".pdf"]`     | Selects every `<a>` element whose `href` attribute value ends with `.pdf`.
`[attribute*=value]` | `a[href*="sometext"]` | Selects every `<a>` element whose `href` attribute value contains the substring `sometext`.

!!! warning "Selector Restriction"

    Selectors can only be used to define a single tag. While you can define `div#id.class[target=_blank]`, you cannot use 'div > p', 'div + p', 'div, p', `div p`, or `div ~ p`.

```yaml
matrix:
- name: mkdocs
  pipeline:
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

## Options

Options      | Type     | Default      | Description
------------ | -------- | ------------ | -----------
`comments`   | bool     | `#!py3 True` | Include comment text in the output.
`attributes` | [string] | `#!py3 []`   | Attributes whose content should be included in the output.
`ignores`    | [string] | `#!py3 []`   | Simple selectors that identify tags to ignore. Only allows tags, IDs, classes, and other attributes.

## Categories

HTML returns text with the following categories.

Category         | Description
---------------- | -----------
`html-content`   | Text captured from HTML blocks.
`html-attribute` | Text captured from HTML attributes.
`html-comment`   | Text captured from HTML comments.
