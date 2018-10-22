# Wildcard

## Usage

The Wildcard plugin is a flow control plugin. It uses [Wildcard Match's `fnmatch` library][fnmatch] to perform wildcard matches on categories passed to it from the pipeline in order to determine if the text should be passed to the next filter.

You can define patterns for the following cases:

- `allow`: the chunk of text is allowed to be evaluated by the next filter.
- `skip`: the chunk of text should skip the next filter.
- `halt`: halts the progress of the text chunk(s) down the pipeline and sends it directly to the spell checker.

Under each option, you can define a list of different patterns. The plugin will loop through the patterns until it has determined what should be done with the text.

The `fnmatch` library is configured with the `NEGATE`, `BRACE` and `IGNORECASE` flags. It also allows you to specify multiple patterns on one line separated with `|`.  See [Wildcard Match's documentation][fnmatch] to learn more about its behavior in regards to features and flags.

In this example, we wish to specifically target inline Python text and ignore `noqa`, `pragma`, and `shebang` lines.  So after the Python step, which returns both docstrings and inline comments, we specify that we only want to allow `py-comment` categories in the next filter. The context filter removes the lines that start with the aforementioned things, and passes the text down the pipe.  The last filter step receives both the `context` text objects **and** the `py-docstrings` from earlier.

```yaml
matrix:
- name: python
  sources:
  - setup.py
  - pyspelling/**/*.py
  aspell:
    lang: en
  dictionary:
    wordlists:
    - docs/src/dictionary/en-custom.txt
    output: build/dictionary/python.dic
  pipeline:
  - pyspelling.filters.python:
  - pyspelling.flow_control.wildcard:
      allow:
      - py-comment
  - pyspelling.filters.context:
      context_visible_first: true
      delimiters:
      # Ignore lint (noqa) and coverage (pragma) as well as shebang (#!)
      - open: ^(?:(?:noqa|pragma)\b|!)
        close: $
      # Ignore Python encoding string -*- encoding stuff -*-
      - open: ^ *-\*-
        close: -\*-$
  - pyspelling.filters.context:
      context_visible_first: true
      escapes: \\[\\`~]
      delimiters:
      # Ignore text between inline back ticks
      - open: (?P<open>`+)
        close: (?P=open)
      # Ignore multiline content between fences ~~~ content ~~~
      - open: (?s)^(?P<open>\s*~{3,})
        close: ^(?P=open)$
```

## Options

Options | Type     | Default       | Description
------- | -------- | ------------- | -----------
`allow` | [string] | `#!py3 ["*"]` | The chunk of text is allowed to be evaluated by the next filter.
`skip`  | [string] | `#!py3 []`    | The chunk of text should skip the next filter.
`halt`  | [string] | `#!py3 []`    | Halts the progress of the text chunk down the pipeline and sends it directly to the spell checker.

--8<-- "refs.txt"
