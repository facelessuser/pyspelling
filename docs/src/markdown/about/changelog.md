# Changelog

## 2.0.0

- **NEW**: (Breaking change) Task names should be unique and using `--name` from the command line will only target one `name` (the last task defined with that name). If you were not using `name` to run a group of tasks, you will not notice any changes.
- **NEW**: Task option `group` has been added to target multiple tasks with the `--group` command line option. `group` name can be shared across different tasks.
- **NEW**: Add XML filter (PySpelling now has a dependency on `lxml`).
- **NEW**: Add Open Document Format (ODF) filter for `.odt`, `.ods`, and `.odp` files.
- **NEW**: Add Office Open XML format (newer Microsoft document format) for `.docx`, `.xlsx`, and `.pptx` files.
- **NEW**: CSS selectors in XML and HTML filters now support `:not()` and `:matches()` pseudo class.
- **NEW**: CSS selectors now support `,` in patterns.
- **NEW**: CSS selectors now support `i` in attribute selectors: `[attr=value i]`.
- **NEW**: CSS selectors now support namespaces (some configuration required).
- **NEW**: For better HTML context, display a tag's ancestry (just tag name of parents).
- **NEW**: Captured tags are now configurable via `captures`, but tags that are not captured still have their children crawled unless they are under `ignores`.
- **NEW**: Support modes added for HTML filter: `html`, `html5`, and `xhtml`.
- **NEW**: `CHECK_BOM` plugin attribute has been deprecated in favor of overriding the exposed `has_bom` function.
- **NEW**: Tasks can be hidden with the `hidden` configuration option. Tasks with `hidden` enabled will only run if they are explicitly called by name.
- **NEW**: Add normal string support to Python filter.
- **NEW**: Add string and template literal support for JavaScript filter.
- **NEW**: Add string support for CPP filter.
- **NEW**: Add `generic_mode` option to CPP to allow for generic C/C++ comment style capture from non C/C++ file types.
- **NEW**: Context will normalize line endings before applying context (can be disabled).
- **NEW**: CPP, Stylesheet, and JavaScript plugins now normalize line endings of block comments.
- **NEW**: UTF-16 and UTF-32 is not really supported by Aspell and Hunspell, so at the end of the pipeline, Unicode strings that have the associated encoding of UTF-16 or UTF-32 will encoding with the compatible UTF-8. This does not apply to files being processed with a disabled pipeline. When the pipeline is disabled, files are sent directly to the spell checker with no modifications.
- **FIX**: Case related issues when comparing tags and attributes in HTML.
- **FIX**: CSS selectors should only compare case insensitive for ASCII characters A-Z and a-z.
- **FIX**: Allow CSS escapes in selectors.
- **FIX**: Don't send empty (or strings that are just whitespace) to spell checker to prevent Aspell 0.50 series from crashing (also to increase performance).
- **FIX**: Catch and bubble up errors better.
- **FIX**: Fix issue where Python module docstrings would not get spell checked if they followed a shebang.

## 1.1.0

- **NEW**: Add URL/email address filter. (#30)
- **NEW**: If `pipeline` configuration key is set to `null`, do not use any filters, and send the filename, not the content, to the spell checker.
- **NEW**: Add `encoding` option to `dictionary` configuration for the purpose of communicating what encoding the main dictionary is when compiling wordlists (only Aspell takes advantage of this).
- **FIX**: Fix Hunspell `-O` option which was mistakenly `-o`. (#31)

## 1.0.0

- **NEW**: Allow multiple names on command line via: `pyspelling -n name1 -n name2`.
- **FIX**: Fix empty HTML tags not properly having their attributes evaluated.
- **FIX**: Fix case where a deprecation warning for `filters` is shown when it shouldn't.
- **FIX**: Better docstring recognition in Python filter.
- **FIX**: Catch comments outside of the `<HTML>` tag.
- **FIX**: Filter out `Doctype`, `CData`, and other XML or non-content type information.

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
