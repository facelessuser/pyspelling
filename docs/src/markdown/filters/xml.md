# XML

## Usage

The XML filter is designed to capture XML content, comments, and even attributes. It allows for filtering out specific tags, and you can even filter them out with CSS selectors (even though this is XML content :slightly_smiling:).

When first in the chain, the XML filter will look for the encoding of the file in its header and convert the buffer to Unicode. It will assume `utf-8` if no encoding header is found, and the user has not overridden the fallback encoding.

The HTML filter uses BeautifulSoup4 to convert the Unicode content to XML structure. Tag content is as one block for the whole file. If enabled, the XML filter will also return chunks for comments and even attributes. Each type of text chunk is returned with their own category type.

Tags can be captured or ignored with the `captures` and `ignores` options. These options work by employing CSS selectors to target the tags. The CSS selectors are based on a limited subset of CSS4 selectors.

```yaml
matrix:
- name: xml
  pipeline:
  - pyspelling.filters.xml:
      comments: false
      attributes:
      - some-data
      ignores:
      - :matches(ignore_tag, [ignore_attribute])
  sources:
  - site/*.xml
```

## Supported CSS Selectors

The CSS selectors are based on a limited subset of CSS4 selectors. The same selectors that are available for HTML are available for XML except for classes and IDs.

Below shows accepted selectors. You must configure the CSS namespaces in the plugin options in order for them to work properly.

While an effort is made to mimic CSS selector behavior, there may be some differences or quirks. We do not support all CSS selector features, but enough to make the task of ignoring tags or selectively capturing tags easy. We particularly do not support notations with ancestry such as `div > p`, `div + p`, `div p`, or `div ~ p`. The only pseudo classes that are currently supported is `:not()` and `:matches()` as they are the most helpful in the task of ignoring or capturing tags.

Examples below are using HTML, but can be adapted for XML.

Selector             | Example                       | Description
-------------------- | ----------------------------- | -----------
`Element`            | `div`                         | Select the `<div>` element (will be under the default namespace if defined for XHTML).
`Element, Element`   | `div, h1`                     | Select the `<div>` element and the `<h1>` element.
`namespace|Element`  | `svg|circle`                  | Select the `<circle>` element which also has the namespace `svg`.
`*|Element`          | `*|div`                       | Select the `<div>` element with or without a namespace.
`namespace|*`        | `svg|*`                       | Select any element with the namespace `svg`.
`|Element`           | `|div`                        | Select `<div>` elements without a namespace.
`|*`                 | `|*`                          | Select any element without a namespace.
`*|*`                | `*|*`                         | Select all elements with any or no namespace.
`*`                  | `*`                           | Select all elements. If a default namespace is defined, it will be any element under the default namespace.
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
`:matches(sel, sel)` | `:matches(div, .some-class)`  | Selects elements that are not `<div>` and do not have class `some-class`.


## Options

Options      | Type     | Default         | Description
------------ | -------- | --------------- | -----------
`comments`   | bool     | `#!py3 True`    | Include comment text in the output.
`attributes` | [string] | `#!py3 []`      | Attributes whose content should be included in the output.
`ignores`    | [string] | `#!py3 []`      | CSS style selectors that identify tags to ignore. Child tags will not be crawled.
`captures`   | [string] | `#!py3 ['*|*']` | CSS style selectors used to narrow which tags that text is collected from. Unlike `ignores`, tags which text is not captured from still have their children crawled.
`namespaces` | dict     | `#!py3 {}`      | Dictionary containing key value pairs of namespaces to use for CSS selectors (equivalent to `@namespace` in CSS). Use the an empty string for the key to define default the namespace. See below for example.
`break_tags` | [string] | `#!py3 []`      | Tags to break on for context. Causes more calls to the spell checker.

!!! example "Namespace example"
    ```
    matrix:
    - name: xml
      pipeline:
      - pyspelling.filters.xml:
          namespaces:
            "": http://www.w3.org/1999/xhtml
            svg: http://www.w3.org/2000/svg
            xlink: http://www.w3.org/1999/xlink
    ```

## Categories

HTML returns text with the following categories.

Category         | Description
---------------- | -----------
`xml-content`   | Text captured from XML tags.
`xml-attribute` | Text captured from XML attributes.
`xml-comment`   | Text captured from XML comments.
