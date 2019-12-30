# Configuration

## Configuration File

PySpelling requires a YAML configuration file. The file defines the various spelling tasks along with their individual
filters and options.

You can optionally specify the preferred spell checker as a global option (`aspell` is the default if not specified).
This can be overridden on the command line.

```yaml
spellchecker: hunspell
```

All of the spelling tasks are contained under the keyword `matrix` and are organized in a list:

```yaml
matrix:
- task1

- task2
```

Each task requires, at the very least, a `name` and `sources` to search.

Depending on your setup, you may need to set the dictionary to use as well. Each spell checker specifies their
dictionary/language differently which is covered in more details in [Spell Checker Options](#spell-checker-options).

```yaml
matrix:
- name: Python Source
  aspell:
    lang: en
  sources:
  - pyspelling/**/*.py
```

You can also define more complicated tasks which will run your text through various filters before performing the spell
checking by providing a custom pipeline.  You can also add your own custom wordlists to extend the dictionary.

```yaml
matrix:
- name: Python Source
  sources:
  - pyspelling/**/*.py
  aspell:
    lang: en
  dictionary:
    wordlists:
    - docs/src/dictionary/en-custom.txt
    output: build/dictionary/python.dic
  pipeline:
  - pyspelling.filters.python:
  - pyspelling.filters.context:
      context_visible_first: true
      escapes: \\[\\`~]
      delimiters:
      # Ignore multiline content between fences (fences can have 3 or more back ticks)
      # ```
      # content
      # ```
      - open: '(?s)^(?P<open> *`{3,})$'
        close: '^(?P=open)$'
      # Ignore text between inline back ticks
      - open: '(?P<open>`+)'
        close: '(?P=open)'
```

### Name

Each spelling tasks *should* have a unique name and is defined with the `name` key.

When using the command line `--name` option, the task with the matching name will be run.

```yaml
matrix:
- name: python
```

!!! new "New Behavior 2.0"
    In `1.0`, names doubled as identifiers and groups. It became apparent for certain features that a unique name is
    desirable for targeting different tasks, while a group specifier should be implemented separately. In `2.0`, if
    multiple tasks have the same name, the last defined one will be the targeted task when requesting a named task. Use
    groups to target multiple grouped tasks.

### Groups

Each task can be assigned to a group. The group name can be shared with multiple tasks. All tasks in a group can be run
by specifying the `--group` option with the name of the group on the command line. This option is only available in
version `1.1` of the configuration file.

```yaml
matrix:
- name: python
  group: some_name
```

!!! new "New 2.0"
    `group` was added in version `2.0`.

### Hidden

All tasks in a configuration file will be run if no `name` is specified. In version `1.1` of the configuration file, If
a task enables the option `hidden` by setting it to `true`, that task will *not* be run automatically when no `name` is
specified. `hidden` tasks will only be run if they are specifically mentioned by `name`.

```yaml
matrix:
- name: python
  hidden: true
```

!!! new "New 2.0"
    `group` was added in version `2.0`.

### Default Encoding

When parsing a file, the encoding detection and translation of the data into Unicode is performed by the first filter in
the pipeline. For instance, if HTML is the first, it may check for a BOM or look at the file's header to find the `meta`
tag that specifies the file's encoding. If all encoding checks fail, the filter will usually apply an appropriate
default encoding for the file content type (usually UTF-8, but check the specific filter's documentation to be sure). If
needed, the filter's default encoding can be overridden in the task via the `default_encoding` key. After the first step
in the pipeline, the text is passed around as Unicode which requires no Unicode detection.

```yaml
matrix:
- name: markdown
  pipeline:
  - pyspelling.filters.text
  sources:
  - '**/*.md'
  default_encoding: utf-8
```

Once all filtering is complete, the text will be passed to the spell checker as byte strings, usually with the
originally detected encoding (unless a filter specifically alters the encoding). The supported spell checkers are
limited to very specific encodings, so if your file is using an unsupported encoding, it will fail.

UTF-16 and UTF-32 is not really supported by Aspell and Hunspell, so at the end of the spell check pipeline, Unicode
strings that have the associated encoding of UTF-16 or UTF-32 will be encoded with the compatible UTF-8. This does not
apply to files being processed with a the pipeline disabled. When the pipeline is disabled, files are sent directly to
the spell checker with no modifications.

!!! tip "Unsupported Encodings"
    If you are trying to spell check a file in an unsupported encoding, you can use the builtin text filter to convert
    the content to a more appropriate encoding. In general, it is recommended to work in, or convert to UTF-8.

### Sources

Each spelling task must define a list of sources to search via the `sources` key. Each source should be a glob pattern
that should match one or more files. PySpelling will perform a search with these patterns to determine which files
should be spell checked.

You can also have multiple patterns on one line separated with `|`. When multiple patterns are defined like this, they
are evaluated simultaneously. This is useful if you'd like to provide an exclusion pattern along with your file pattern.
For instance, if we wanted to scan all python files in our folder, but exclude any in the build folder, we could provide
the following pattern: `**/*.py|!build/*`.

PySpelling uses [Wildcard Match's `glob` library][glob] to perform the file globbing.  By default, it uses the `NEGATE`,
`GLOBSTAR`, and `BRACE` flags, but you can override the flag options with the `glob_flags` option. You can specify the
flags by either their long name `GLOBSTAR` or their short name `G`. See [Wildcard Match's documentation][glob] for more
information on the available flags and what they do.

```yaml
matrix:
- name: python
  pipeline:
  - pyspelling.filters.python:
      comments: false
  glob_flags: N|G|B
  sources:
  - pyspelling/**/*.py
```

### Expect Match

When processing the sources field it is expected to find at least
one matching file. If no files are located it can be helpful to raise an error
and this is the default behaviour. If it is not expected to always find a file
then the `expect_match` configuration can be used to suppress the error.

```yaml
matrix:
- name: markdown
  pipeline:
  - pyspelling.filters.text
  sources:
  - '**/*.md'
  expect_match: false
  default_encoding: utf-8
```

### Pipeline

PySpelling allows you to define tasks that outline what kind of files you want to spell check, and then sends them down
a pipeline that filters the content returning chunks of text with some associated context. Each chunk is sent down each
step of the pipeline until it reaches the final step, the spell check step. Between filter steps, you can also insert
flow control steps that allow you to have certain text chunks skip specific steps. All of this is done with
[pipeline plugins](./pipeline.md).

Let's say you had some Markdown files and wanted to convert them to HTML, and then filter out specific tags. You could
just use the Markdown filter to convert the file to HTML and then pass it through the HTML filter to extract the text
from the HTML tags.

```yaml
matrix:
- name: markdown
  sources:
  - README.md
  pipeline:
  - pyspelling.filters.markdown:
  - pyspelling.filters.html:
      comments: false
      attributes:
      - title
      - alt
      ignores:
      - code
      - pre
```

If needed, you can also insert flow control steps before certain filter steps. Each text chunk that is passed between
filters has a category assigned to it from the previous filter. Flow control steps allow you to restrict the next filter
to specific categories, or exclude specific categories from the next step. This is covered in more depth in
[Flow Control](./pipeline.md#flow-control).

If for some reason you need to send the file directly to the spell checker without using PySpelling's pipeline, simply
set `pipeline` to `null`. This sends file directly to the spell checker without evaluating the encoding or passing
through any filters. Specifically with Hunspell, it also sends the spell checker the filename instead of piping the
content as Hunspell has certain features that don't work when piping the data, such as OpenOffice ODF input. 

Below is an example where we send an OpenOffice ODF file directly to Hunspell in order to use Hunspell's `-O` option to
parse the ODF file. Keep in mind that when doing this, no encoding is sent to the spell checker unless you define
`default_encoding`. If `default_encoding` is not defined, PySpelling will decode the returned content with the
terminal's encoding (or what it thinks the terminal's encoding is).

```yaml
matrix:
- name: openoffice_ODF
  sources:
  - file.odt
  hunspell:
    d: en_US
    O: true
  pipeline: null
```

### Dictionaries and Personal Wordlists

By default, PySpelling sets your main dictionary to `en` for Aspell and `en_US` for Hunspell. If you do not desire an
American English dictionary, or these dictionaries are not installed in their expected default locations, you will need
to configure PySpelling so it can find your preferred dictionary. Since dictionary configuring varies for each spell
checker, the main dictionary is configuration (and virtually any spell checker specific option) is performed via
[Spell Checker Options](#spell-checker-options).

For Aspell, you would use the command line option `--lang` or `-l`, which in the YAML configuration file is `lang` or
`l` respectively. You can see we are just removing the leading `-` characters.

```yaml
matrix:
- name: python
  aspell:
    lang: en
```

For Hunspell, you would use the command line option `-d`, which in the YAML configuration file is `d`:

```yaml
matrix:
- name: python
  hunspell:
    d: en_US
```

While the dictionaries cover a number of commonly used words, they are usually not sufficient. Luckily, both Aspell and
Hunspell allow for adding custom wordlists. You can have as many wordlists as you like, and they can be included in a
list under the key `wordlists` which is also found under the key `dictionary`. While Hunspell doesn't directly compile
the wordlists, Aspell does, and it uses the main dictionary that you have specified to accomplish this.

All the wordlists are combined into one custom dictionary file whose output name and location is defined via the
`output` key which is also found under the `dictionary` key.

Lastly, you can set the encoding to be used during compilation via the `encoding` under `dictionary`. The encoding
should generally match the encoding of your main dictionary. The default encoding is `utf-8`, and only Aspell uses this
option.

```yaml
matrix:
- name: python
  sources:
  - pyspelling/**/*.py
  aspell:
    lang: en
  dictionary:
    wordlists:
    - docs/src/dictionary/en-custom.txt
    output: build/dictionary/python.dic
    encoding: utf-8
  pipeline:
  - pyspelling.filters.python:
      comments: false
```

### Spell Checker Options

Since PySpelling is a wrapper around both Aspell and Hunspell, there are a number of spell checker specific options. As
only a few options are present in both, it was decided to expose them via spell checker specific keywords: `aspell` and
`hunspell` for Aspell and Hunspell respectively. Here you can set options like the default dictionary and search
options. Not all options are exposed though, only relevant search options are passed directly to the spell checker.
Things like replace options (which aren't relevant in PySpelling) and encoding (which are handled internally by
PySpelling) are not accessible.

Spell checker specific options basically translate directly to the spell checker's command line options and only
requires you to remove the leading `-`s you would normally specify on the command line. For instance, a short form
option such as `-l` would simply be represented with the keyword `l`, and the long name form of the same option `--lang`
would be represented as `lang`. Following the key, you would provide the appropriate value depending on it's
requirement.

Boolean flags would be set to `true`.

```yaml
matrix:
- name: html
  sources:
  - docs/**/*.html
  aspell:
    H: true
  pipeline:
  - pyspelling.filters.html
```

Other options would be set to a string or an integer value.

```yaml
matrix:
- name: python
  sources:
  - pyspelling/**/*.py
  aspell:
    lang: en
  pipeline:
  - pyspelling.filters.python:
      strings: false
      comments: false
```

Lastly, if you have an option that can be used multiple times, just set the value up as an array, and the option will
be added for each value in the array. Assuming you had multiple pre-compiled dictionaries, you could add them under
Aspell's `--add-extra-dicts` option:

```yaml
matrix:
- name: Python Source
  sources:
  - pyspelling/**/*.py
  aspell:
    add-extra-dicts:
    - my-dictionary.dic
    - my-other-dictionary.dic
  pipeline:
```

The above options would be equivalent to doing this from the command line:

```
aspell --add-extra-dicts my-dictionary.doc --add-extra-dicts my-other-dictionary.dic
```

--8<-- "refs.txt"
