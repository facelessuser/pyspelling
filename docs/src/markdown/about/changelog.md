# Changelog

## 2.7.3

- **FIX**: Fix context reporting in the XML, HTML, and other filters derived from XML the filter.

## 2.7.2

- **FIX**: Add note in `--help` option about `--source` behavior.
- **FIX**: Better documentation on language options and Unicode normalization in international languages.

## 2.7.1

- **FIX**: Allow camel case options in Aspell.

## 2.7

- **NEW**: Check for `.pyspelling.yml` or `.pyspelling.yaml` by default.
- **FIX**: Fix documentation about how to specify languages in Aspell and how to specify languages when compiling custom
  wordlists. In short, `d` should be used for specifying languages in general, but when using custom wordlists, `lang`
  should be specified, and it should reference the `.dat` file name..
- **FIX**: Fix spelling in help output.
- **FIX**: Raise error in cases where pipeline options are not indented enough and parsed as an additional pipeline
  name.
- **FIX**: Drop Python 3.5 support and officially support Python 3.9.

## 2.6.1

- **FIX**: Upgrade to `wcmatch` 6.0.3 which fixes issues dealing with dot files and globstar (`**`) when dot globbing is
  not enabled. Also fixes a small logic error with symlink following and globstar. 6.0.3 is now the minimum requirement.

## 2.6

- **NEW**: Add support for `wcmatch` version `6.0`.
- **NEW**: `wcmatch` version `6.0` adds a default pattern limit of `1000` to help protect against really large pattern
  expansions such as `{1..1000000}`. If you wish to control this default, or disable it entirely, you can via the new
  `glob_pattern_limit` configuration option.

## 2.5.1

- **FIX**: Add workaround for `wcmatch` version `5.0`.

## 2.5

- **NEW**: Add `expect_match` option to prevent a rule from failing if it finds no matching files.
- **NEW**: Formally support Python 3.8.

## 2.4

- **NEW**: Disable Aspell filters by default. Users must explicitly set the `mode` parameter under the `aspell` option
  to enable default Aspell filters.
- **New**: Throw an exception with a message if no configuration is found or there is some other issue.
- **New**: Throw an exception with a message when no tasks are found in the matrix or when no tasks match a given name
  or group.
- **New**: Throw an exception with a message when a task is run but no files are found.

## 2.3.1

- **FIX**: Properly handle docstring content and detection in files that have single line functions.

## 2.3

- **NEW**: Support new `wcmatch` glob feature flags and upgrade to `wcmatch` 4.0.
- **FIX**: Don't use recursion when parsing XML or HTML documents.

## 2.2.6

- **FIX**: Require `wcmatch` 3.0 for `glob` related fixes.

## 2.2.5

- **FIX**: Rework comment extraction in XML plugin.
- **FIX**: Newer versions of Soup Sieve will not compile an empty string, so adjust XML and HTML plugin logic to account
  for this behavior.

## 2.2.4

- **FIX**: Explicitly require Beautiful Soup 4 dependency.

## 2.2.3

- **FIX**: There is no need to un-escape content for HTML/XML as it is already un-escaped in the `bs4` objects.
- **FIX**: Upgrade to latest beta of Soup Sieve.

## 2.2.2

- **FIX**: Fix `:empty` and `:root` and `:nth-*` selectors not working properly without a tag name specified before.
  This is now done via our external lib called `soupsieve` which is the same homegrown CSS library that we were using
  internally.

- **FIX**: Potential infinite loop when using `:nth-child()`.

## 2.2.1

- **FIX**: Comments in HTML/XML should be returned regardless of whether they are in an ignored tag or not.

## 2.2

- **NEW**: Add support for CSS4 selectors: `:empty`, `:first-child`, `:last-child`, `:only-child`, `:first-of-type`,
  `:last-of-type`, `:only-of-type`, `:nth-child(an+b [of S]?)`, `:nth-last-child(an+b [of S]?)`, `:nth-of-type(an+b)`,
  and `:nth-last-of-type(an+b)`. (#58)

## 2.1.1

- **FIX**: CSS4 allows `:not()`, `:has()`, and `:is()` to be nested in `:not()`. (#62)

## 2.1

- **NEW**: Add support for `div p`, `div>p`, `div+p`, `div~p` in the HTML/XML filter's CSS selectors. (#51)
- **NEW**: Add support for the `:root` CSS selector. (#57)
- **NEW**: Add support for experimental `:has()` selector. (#54)
- **FIX**: According to CSS4 specification, `:is()` is the final name for `:matches()` but the `:matches()` is an
  allowed alias. (#53)
- **FIX**: Allow `:not()` to be nested in `:is()`/`:matches()`. (#56)

## 2.0

- **NEW**: (Breaking change) Task names should be unique and using `--name` from the command line will only target one
  `name` (the last task defined with that name). If you were not using `name` to run a group of tasks, you will not
  notice any changes.
- **NEW**: Task option `group` has been added to target multiple tasks with the `--group` command line option. `group`
  name can be shared across different tasks.
- **NEW**: Add XML filter (PySpelling now has a dependency on `lxml`).
- **NEW**: Add Open Document Format (ODF) filter for `.odt`, `.ods`, and `.odp` files.
- **NEW**: Add Office Open XML format (newer Microsoft document format) for `.docx`, `.xlsx`, and `.pptx` files.
- **NEW**: CSS selectors in XML and HTML filters now support `:not()` and `:matches()` pseudo class.
- **NEW**: CSS selectors now support `,` in patterns.
- **NEW**: CSS selectors now support `i` in attribute selectors: `[attr=value i]`.
- **NEW**: CSS selectors now support namespaces (some configuration required).
- **NEW**: For better HTML context, display a tag's ancestry (just tag name of parents).
- **NEW**: Captured tags are now configurable via `captures`, but tags that are not captured still have their children
  crawled unless they are under `ignores`.
- **NEW**: Support modes added for HTML filter: `html`, `html5`, and `xhtml`.
- **NEW**: `CHECK_BOM` plugin attribute has been deprecated in favor of overriding the exposed `has_bom` function.
- **NEW**: Tasks can be hidden with the `hidden` configuration option. Tasks with `hidden` enabled will only run if they
  are explicitly called by name.
- **NEW**: Add normal string support to Python filter.
- **NEW**: Add string and template literal support for JavaScript filter.
- **NEW**: Add string support for CPP filter.
- **NEW**: Add `generic_mode` option to CPP to allow for generic C/C++ comment style capture from non C/C++ file types.
- **NEW**: Context will normalize line endings before applying context (can be disabled).
- **NEW**: CPP, Stylesheet, and JavaScript plugins now normalize line endings of block comments.
- **NEW**: UTF-16 and UTF-32 is not really supported by Aspell and Hunspell, so at the end of the pipeline, Unicode
  strings that have the associated encoding of UTF-16 or UTF-32 will encoding with the compatible UTF-8. This does not
  apply to files being processed with a disabled pipeline. When the pipeline is disabled, files are sent directly to the
  spell checker with no modifications.
- **FIX**: Case related issues when comparing tags and attributes in HTML.
- **FIX**: CSS selectors should only compare case insensitive for ASCII characters A-Z and a-z.
- **FIX**: Allow CSS escapes in selectors.
- **FIX**: Don't send empty (or strings that are just whitespace) to spell checker to prevent Aspell 0.50 series from
  crashing (also to increase performance).
- **FIX**: Catch and bubble up errors better.
- **FIX**: Fix issue where Python module docstrings would not get spell checked if they followed a shebang.

## 1.1

- **NEW**: Add URL/email address filter. (#30)
- **NEW**: If `pipeline` configuration key is set to `null`, do not use any filters, and send the filename, not the
  content, to the spell checker.
- **NEW**: Add `encoding` option to `dictionary` configuration for the purpose of communicating what encoding the main
  dictionary is when compiling wordlists (only Aspell takes advantage of this).
- **FIX**: Fix Hunspell `-O` option which was mistakenly `-o`. (#31)

## 1.0

- **NEW**: Allow multiple names on command line via: `pyspelling -n name1 -n name2`.
- **FIX**: Fix empty HTML tags not properly having their attributes evaluated.
- **FIX**: Fix case where a deprecation warning for `filters` is shown when it shouldn't.
- **FIX**: Better docstring recognition in Python filter.
- **FIX**: Catch comments outside of the `<HTML>` tag.
- **FIX**: Filter out `Doctype`, `CData`, and other XML or non-content type information.

## 1.0b2

- **FIX**: Fix CPP comment regular expression.

## 1.0b1

- **NEW**: Better context for HTML elements. HTML is now returned by block level elements, and the elements selector is
  given as context. Attributes also return a selector as context and are returned individually. HTML comments are
  returned as individual hunks.
- **NEW**: Add Stylesheet and CPP filters (#17)
- **NEW**: JavaScript is now derived from CPP.
- **NEW**: PySpelling looks for `.spelling.yml` or `.pyspelling.yml` with a priority for the latter. (#12)
- **NEW**: Spelling pipeline adjustments: you can now explicitly allow only certain categories, skip categories, or halt
  them in the pipeline. Pipeline flow control is now done via a new `FlowControl` plugin. When avoiding, including, or
  skipping categories, they are now done with wildcard patterns. (#16)
- **NEW**: Drop scanning python normal strings in plugin.
- **NEW**: Use `get_plugin` instead of `get_filter`, but allow a backwards compatible path for now.
- **NEW**: In configuration, `documents` is now `matrix` and `filters` is now `pipeline`, but a deprecation path has
  been added. (#15)
- **NEW**: Provide a class attribute that will cause a Filter object to avoid BOM detection if it is not appropriate for
  the given file.
- **NEW**: Wordlists should get the desired language/dictionary from the spell checker specific options.
- **NEW**: Add global configuration option to specify the preferred spell checker, but it is still overridable via
  command line.
- **FIX**: Internal cleanup in regards to error handling and debug.
- **FIX**: Fix context issue when no escapes are defined.

## 0.2a4

- **NEW**: Text filter can handle Unicode normalization and converting to other encodings.
- **NEW**: Default encoding is now `utf-8` for all filters.
- **FIX**: Internal encoding handling.

## 0.2a3

- **FIX**: Text filter was returning old Parser name instead of new Filter name.

## 0.2a2

- **NEW**: Incorporate the Decoder class into the filter class.
- **NEW**: Add Hunspell support.
- **NEW**: Drop specifying spell checker in configuration file. It must be set from command line.
- **FIX**: Add missing documentation about Context filter.

## 0.2a1

- **NEW**: Better filters (combine filters and parsers into just filters).
- **NEW**: Drop Python 2 support.
- **NEW**: Better Python encoding detection.
- **NEW**: Better HTML encoding detection.
- **NEW**: Drop `file_extensions` option and `parser` option.
- **NEW**: Filters no longer define file extensions. Sources must specify a wildcard path that matches desired files.
- **NEW**: Drop regular expression support for sources.
- **NEW**: Drop raw filter.

## 0.1a3

- **NEW**: Add JavaScript parser.

## 0.1a2

- **NEW**: Add option to group consecutive Python comments.
- **FIX**: Properly return error.
- **FIX**: Only retry with default encoding if exception thrown was a `UnicodeDecodeError`.

## 0.1a1

- **NEW**: Initial alpha release.
