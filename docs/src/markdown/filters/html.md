# HTML

## Usage
The HTML filter is designed to capture HTML content, comments, and even attributes. It allows for filtering out specific tags, and you can even filter them out with basic selectors.

When first in the chain, the HTML filter will look for the encoding of the HTML in its header and convert the buffer to Unicode. It will assume `utf-8` if no encoding header is found, and the user has not overridden the fallback encoding.

The HTML filter uses BeautifulSoup4 to convert the Unicode content to HTML. Content is returned in individual chunks by block tags. If enabled the HTML filter will also return chunks for comments and even attributes. Each type of text chunk is returned with their own category type.

Tags can be ignored with basic CSS selectors.

Below shows accepted selectors. When speaking about namespaces, they only apply to XHTML or when dealing with recognized foreign tags in HTML5. You must configure the CSS namespaces in the plugin options in order for them to work properly.

While an effort is made to mimic CSS selector behavior, there may be some differences. We do not support all CSS selector features, but enough to make the task of ignoring tags or selectively capturing tags easy.

Selector             | Example               | Description
-------------------- | --------------------- | -----------
`Element`            | `div`                 | Select the `<div>` element (will be under the default namespace if defined for XHTML).
`namespace|Element`  | `svg|div`             | Select the `<div>` element which also has the namespace `svg`.
`*|Element`          | `*|div`               | Select the `<div>` element with or without a namespace.
`namespace|*`        | `svg|*`               | Select any element with the namespace `svg`.
`|Element`           | `|div`                | Select `<div>` elements without a namespace.
`|*`                 | `|*`                  | Select any element without a namespace.
`*|*`                | `*|*`                 | Select all elements with any or no namespace.
`*`                  | `*`                   | Select all elements. If a default namespace is defined, it will be any element under the default namespace.
`.class`             | `.some-class`         | Select all elements with the class `some-class`.
`#id`                | `#some-id`            | Select the element with the ID `some-id`.
`[attribute]`        | `[target]`            | Selects all elements with a `target` attribute.
`[ns|attribute]`     | `[svg|circle]`        | Selects `circle` element under the `svg` namespace (assuming it has been configured in the `namespaces` option).
`[*|attribute]`      | `[*|a]`               | Selects any element `a` that has a namespace or not.
`[|attribute]`       | `[|a]`                | Selects `a` element as `[|a]` is equivalent to `[a]`.
`[attribute=value]`  | `[target=_blank]`     | Selects all elements with `target="_blank"`.
`[attribute~=value]` | `[title~=flower]`     | Selects all elements with a title attribute containing the word `flower`.
`[attribute|=value]` | `[lang|=en]`          | Selects all elements with a `lang` attribute value starting with `en`.
`[attribute^=value]` | `a[href^="https"]`    | Selects every `<a>` element whose `href` attribute value begins with `https`.
`[attribute$=value]` | `a[href$=".pdf"]`     | Selects every `<a>` element whose `href` attribute value ends with `.pdf`.
`[attribute*=value]` | `a[href*="sometext"]` | Selects every `<a>` element whose `href` attribute value contains the substring `sometext`.

!!! warning "Selector Restriction"

    Currently, selectors can only be used to define a single tag. While you can specify `div#id.class[target=_blank]`, you cannot use `div > p`, `div + p`, `div, p`, `div p`, or `div ~ p`. Ancestry is not available at time of tag evaluation.

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

Options      | Type     | Default       | Description
------------ | -------- | ------------- | -----------
`comments`   | bool     | `#!py3 True`  | Include comment text in the output.
`attributes` | [string] | `#!py3 []`    | Attributes whose content should be included in the output.
`ignores`    | [string] | `#!py3 []`    | Simple selectors that identify tags to ignore. Child tags will not be crawled.
`captures`   | [string] | `#!py3 []`    | Simple selectors used to narrow which tags that text is collected from. Unlike `ignores`, tags which text is not captured still have their children crawled.
`mode`       | string   | `#!py3 'html` | Mode to use when parsing HTML: `html`, `xhtml`, `html5`.
`namespaces` | dict     | `#!py3 {}`    | Dictionary containing key value pairs of namespaces to use for CSS selectors (equivalent to `@namespace` in CSS). Use the an empty string for the key to define default the namespace. See below for example.

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
