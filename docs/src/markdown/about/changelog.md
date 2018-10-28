# Changelog

## 1.0.0

- **NEW**: Allow multiple names on command line via: `pyspelling -n name1 -n name2`.

## 1.0.0b2

- **FIX**: Fix CPP comment regular expression.

## 1.0.0b1

- **NEW**: Better context for HTML elements. HTML is now returned by block level elements, and the elements selector is given as context. Attributes also return a selector as context and are returned individually. HTML comments are returned as individual hunks.
- **NEW**: Add Stylesheet and CPP filters (#17)
- **NEW**: JavaScript is now derived from CPP.
- **NEW**: PySpelling looks for `.spelling.yml` or `.pyspelling.yml` with a priority for the latter. (#12)
- **NEW**: Spelling pipeline adjustments: you can now explicitly allow only certain categories, skip categories, or halt them in the pipeline. Pipeline flow control is now done via a new `FlowControl` plugin. When avoiding, including, or skipping categories, they are now done with wildcard patterns. (#16)
- **NEW**: Drop scanning python normal strings in plugin.
- **NEW**: Use `get_plugin` instead of `get_filter`, but allow a backwards compatible path for now.
- **NEW**: In configuration, `documents` is now `matrix` and `filters` is now `pipeline`, but a deprecation path has been added. (#15)
- **NEW**: Provide a class attribute that will cause a Filter object to avoid BOM detection if it is not appropriate for the given file.
- **NEW**: Wordlists should get the desired language/dictionary from the spell checker specific options.
- **NEW**: Add global configuration option to specify the preferred spell checker, but it is still overridable via command line.
- **FIX**: Internal cleanup in regards to error handling and debug.
- **FIX**: Fix context issue when no escapes are defined.

## 0.2.0a4

- **NEW**: Text filter can handle Unicode normalization and converting to other encodings.
- **NEW**: Default encoding is now `utf-8` for all filters.
- **FIX**: Internal encoding handling.

## 0.2.0a3

- **FIX**: Text filter was returning old Parser name instead of new Filter name.

## 0.2.0a2

- **NEW**: Incorporate the Decoder class into the filter class.
- **NEW**: Add Hunspell support.
- **NEW**: Drop specifying spell checker in configuration file. It must be set from command line.
- **FIX**: Add missing documentation about Context filter.

## 0.2.0a1

- **NEW**: Better filters (combine filters and parsers into just filters).
- **NEW**: Drop Python 2 support.
- **NEW**: Better Python encoding detection.
- **NEW**: Better HTML encoding detection.
- **NEW**: Drop `file_extensions` option and `parser` option.
- **NEW**: Filters no longer define file extensions. Sources must specify a wildcard path that matches desired files.
- **NEW**: Drop regular expression support for sources.
- **NEW**: Drop raw filter.

## 0.1.0a3

- **NEW**: Add JavaScript parser.

## 0.1.0a2

- **NEW**: Add option to group consecutive Python comments.
- **FIX**: Properly return error.
- **FIX**: Only retry with default encoding if exception thrown was a `UnicodeDecodeError`.

## 0.1.0a1

- **NEW**: Initial alpha release.
