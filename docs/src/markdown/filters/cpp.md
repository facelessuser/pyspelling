# CPP

## Usage

The CPP plugin is designed to find and return C/C++ style comments. When first in the chain, the CPP filter uses no
special encoding detection. It will assume `utf-8` if no encoding BOM is found, and the user has not overridden the
fallback encoding. Text is returned in chunks based on the context of the text: block, inline, or string (if enabled).

When the `strings` [option](#options) is enabled, content will be extracted from strings (not character constants).
Support is available for all the modern C++ strings shown below. CPP will also handle decoding string escapes as well,
but as string character width and encoding can be dependent on implementation and configuration, some additional setup
may be required via [option](#options). Strings will be returned with the specified encoding, even if it differs from
the file's encoding (this is the associated encoding specified in the `SourceText` object, the content itself is still
in Unicode).

```c++
    auto s0 =    "Narrow character string";                   // char
    auto s1 =   L"Wide character string";                     // wchar_t
    auto s2 =  u8"UTF-8 strings";                             // char
    auto s3 =   u"UTF-16 strings";                            // char16_t
    auto s4 =   U"UTF-32 strings";                            // char32_t
    auto R0 =   R"("Raw strings")";                           // const char*
    auto R1 =   R"delim("Raw strings with delimiters")delim"; // const char*
    auto R3 =  LR"("Raw wide character strings")";            // const wchar_t*
    auto R4 = u8R"("Raw UTF-8 strings")";                     // const char*, encoded as UTF-8
    auto R5 =  uR"("Raw UTF-16 strings")";                    // const char16_t*, encoded as UTF-16
    auto R6 =  UR"("Raw UTF-32 strings")";                    // const char32_t*, encoded as UTF-32
```

As C++ style comments are fairly common convention in other languages, this filter can often be used for other languages
as well using `generic_mode`. In Generic Mode, many C/C++ specific considerations and options will be disabled. See
[Generic Mode](#generic-mode) for more information.

```yaml
matrix:
- name: cpp
  pipeline:
  - pyspelling.filters.cpp
      line_comments: false
  sources:
  - js_files/**/*.{cpp,hpp,c,h}
```

## Filtering String types

When `strings` is enabled, you can specify which strings you want to allow via the `string_types` option. Valid string
types are `S` for standard, `L` for long/wide, `U` for Unicode (all variants), and `R` for raw.  Case is not important,
and the default value is `sul`.  

If specifying `R`, you must also specify either `U`, `L`, or `S` as raw strings are also either `S`, `L`, or `S`
strings. Selecting `UR` will select both Unicode strings and Unicode raw strings. If you need to target just raw
strings, you can use `R*` which will target all raw string types: raw Unicode, raw wide, and raw standard. You can use
`*` for other types as well. You can also just specify `*` by itself to target all string types.

## Generic Mode

C/C++ style comments are not exclusive to C/C++. Many different file types have adopted similar style comments. The CPP
filter has a generic mode which allows for a C/C++ style comment extraction without all the C/C++ specific
considerations. Simply enable `generic_mode` via the [options](#options).

Generic Mode disables the C/C++ specific nuance of allowing multiline comments via escaping newlines. This is a very
C/C++ specific thing that is rarely carried over by others that have adopted C/C++ style comments:

```c++
// Generic mode will \
   not allow this.
```

Generic Mode will not decode any character escapes in strings when enabled. C/C++ has very specific rules for handling
string escapes, only a handful of which may translate to other languages. Generic Mode is mainly meant for comments and
not strings, but will return content of single quoted and double quoted strings if `strings` is enabled. All related
escape decoding options do not apply to Generic Mode.

Trigraphs are very C/C++ specific, and will never be evaluated in Generic Mode.

Lastly, when using this filter in Generic Mode, you can also adjust the category prefix from `cpp` to whatever you would
like via the `prefix` [option](#options).

## Options

Options            | Type     | Default         | Description
------------------ | -------- | --------------- | -----------
`block_comments`   | bool     | `#!py3 True`    | Return `SourceText` entries for each block comment.
`line_comments`    | bool     | `#!py3 True`    | Return `SourceText` entries for each line comment.
`strings`          | bool     | `#!py3 False`   | Return `SourceText` entries for each string.
`group_comments`   | bool     | `#!py3 False`   | Group consecutive inline comments as one `SourceText` entry.
`trigraphs`        | bool     | `#!py3 False`   | Account for trigraphs in C/C++ code. Trigraphs are never evaluated in [Generic Mode](#generic-mode).
`generic_mode`     | bool     | `#!py3 False`   | Parses files with a generic C++ like mode for parsing C++ style comments from non C++ files. See [Generic Mode](#generic-mode) for more info.
`decode_escapes`   | bool     | `#!py3 True`    | Enable/disable string escape decoding. Strings are never decoded in [Generic Mode](#generic-mode).
`charset_size`     | int      | `#!py3 1`       | Set normal string character byte width.
`exec_charset`     | string   | `#!py3 'utf-8`  | Set normal string encoding.
`wide_charset_size`| int      | `#!py3 4`       | Set wide string character byte width.
`wide_exec_charset`| string   | `#!py3 'utf-32` | Set wide string encoding.
`string_types`     | string   | `#!py3 "sul"`   | Set the allowed string types to capture: standard strings (`s`),  wide (`l`), Unicode (`u`), and raw (`r`). `*` captures all strings, or when used with a type, captures all variants of that type `r*`.
`prefix`           | string   | `#!py3 'cpp'`   | Change the category prefix.

## Categories

CPP returns text with the following categories. `cpp` prefix can be changed via the `prefix` [option](#options).

Category            | Description
------------------- | -----------
`cpp-block-comment` | Text captured from C++ style block comments.
`cpp-line-comment`  | Text captured from C++ style line comments.
`cpp-string`        | Text captured from strings.
