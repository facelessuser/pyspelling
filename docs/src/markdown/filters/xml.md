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

The CSS selectors are based on a limited subset of CSS4 selectors. Support is provided via Soup Sieve. Please reference [Soup Sieve's documentation][soup-sieve] for more info.

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

--8<--
refs.md
--8<--
