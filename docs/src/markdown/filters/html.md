# HTML

## Usage

The HTML filter is designed to capture HTML content, comments, and even attributes. It allows for filtering out specific tags, and you can even filter them out with basic selectors.

When first in the chain, the HTML filter will look for the encoding of the HTML in its header and convert the buffer to Unicode. It will assume `utf-8` if no encoding header is found, and the user has not overridden the fallback encoding.

The HTML filter uses BeautifulSoup4 to convert the Unicode content to HTML. Content is returned in individual chunks by block tags. While this causes more overhead, as each block is processed individually through the command line tool, it provides context for where the spelling errors are. If enabled, the HTML filter will also return chunks for comments and even attributes. Each type of text chunk is returned with their own category type.

Tags can be captured or ignored with the `captures` and `ignores` options. These options work by employing CSS selectors to target the tags. The CSS selectors are based on a limited subset of CSS4 selectors.

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

The CSS selectors are based on a limited subset of CSS4 selectors.

Below shows accepted selectors. When speaking about namespaces, they only apply to XHTML or when dealing with recognized foreign tags in HTML5. You must configure the CSS namespaces in the plugin options in order for them to work properly.

While an effort is made to mimic CSS selector behavior, there may be some differences or quirks. We do not support all CSS selector features, but enough to make the task of ignoring tags or selectively capturing tags easy. The only pseudo classes that are currently supported is `:not()` and `:matches()` as they are the most helpful in the task of ignoring or capturing tags.

Selector             | Example                       | Description
-------------------- | ----------------------------- | -----------
`Element`            | `div`                         | Select the `<div>` element (will be under the default namespace if defined for XHTML).
`Element, Element`   | `div, h1`                     | Select the `<div>` element and the `<h1>` element.
`Element Element`    | `div p`                       | Select all `<p>` elements inside `<div>` elements.
`Element>Element`    | `div > p`                     | Select all `<p>` elements where the parent is a `<div>` element.
`Element+Element`    | `div + p`                     | Select all `<p>` elements that are placed immediately after `<div>` elements.
`Element~Element`    | `p ~ ul`                      | Select every `<ul>` element that is preceded by a `<p>` element.
`namespace|Element`  | `svg|circle`                  | Select the `<circle>` element which also has the namespace `svg`.
`*|Element`          | `*|div`                       | Select the `<div>` element with or without a namespace.
`namespace|*`        | `svg|*`                       | Select any element with the namespace `svg`.
`|Element`           | `|div`                        | Select `<div>` elements without a namespace.
`|*`                 | `|*`                          | Select any element without a namespace.
`*|*`                | `*|*`                         | Select all elements with any or no namespace.
`*`                  | `*`                           | Select all elements. If a default namespace is defined, it will be any element under the default namespace.
`.class`             | `.some-class`                 | Select all elements with the class `some-class`.
`#id`                | `#some-id`                    | Select the element with the ID `some-id`.
`[attribute]`        | `[target]`                    | Selects all elements with a `target` attribute.
`[ns|attribute]`     | `[xlink|href]`                | Selects elements with the attribute `href` and the namespace `xlink` (assuming it has been configured in the `namespaces` option).
`[*|attribute]`      | `[*|name]`                    | Selects any element with a `name` attribute that has a namespace or not.
`[|attribute]`       | `[|name]`                     | Selects any element with a `name` attribute. `[|name]` is equivalent to `[name]`.
`[attribute=value]`  | `[target=_blank]`             | Selects all attributes with `target="_blank"`.
`[attribute~=value]` | `[title~=flower]`             | Selects all elements with a `title` attribute containing the word `flower`.
`[attribute|=value]` | `[lang|=en]`                  | Selects all elements with a `lang` attribute value starting with `en`.
`[attribute^=value]` | `a[href^="https"]`            | Selects every `<a>` element whose `href` attribute value begins with `https`.
`[attribute$=value]` | `a[href$=".pdf"]`             | Selects every `<a>` element whose `href` attribute value ends with `.pdf`.
`[attribute*=value]` | `a[href*="sometext"]`         | Selects every `<a>` element whose `href` attribute value contains the substring `sometext`.
`:not(sel, sel)`     | `:not(.some-class, #some-id)` | Selects elements that do not have class `some-class` and ID `some-id`.
`:is(sel, sel)`      | `:is(div, .some-class)`       | Selects elements that are not `<div>` and do not have class `some-class`. The alias `:matches` is allowed as well.
`:has(> sel, + sel)` | `:has(> div, + p)`            | Selects elements that have a direct child that is a `<div>` or that have sibling of `<p>` immediately following.
`:root`              | `:root`                       | Selects the root element. In HTML, this is usually the `<html>` element.

!!! new "New 2.1.0"
    Support for `div p`, `div>p`, `div+p`, `div~p`, `:is()`, `:has()` and `:root`.

!!! warning ":has()"
    `:has()` implementation is experimental and may change. There are currently no reference implementation available in any browsers, not to mention the CSS4 specifications have not been finalized, so current implementation is based on our best interpretation.

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
    ```
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
