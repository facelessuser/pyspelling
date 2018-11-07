# Spelling Pipeline

## Overview

PySpelling's pipeline utilizes special plugins to provide [text filtering](#filters) and to [control the flow](#flow-control) of the text down the pipeline. The plugins can be arranged in any order and even included multiple times, the only restriction is that you can't start the pipeline with `FlowControl` plugins, the first plugin must be a `Filter` plugin.

A number of plugins are included with PySpelling, but additional plugins can be written using the [plugin API](./api.md).

## Filter

`Filter` plugins are used to augment and/or filter a given chunk of text returning only the portions that are desired. Once a plugin is done with the text, it passes it down the pipeline. A filter may return one or many chunks, each with a little contextual information. Some filters may return only one chunk of text that is the entirety of the file, and some may return context specific chunks: one for each docstring, one for each comment, etc. The metadata associated with the chunks can also be used by `FlowControl` plugins to allow certain types of text to skip certain filters.

Aside from filtering the text, the first filter in the pipeline is always responsible for initially reading the file from disk and getting the file content into a Unicode buffer that PySpelling can work with. It is also responsible for setting the default encoding and/or identifying the encoding from the file header if there is special logic to determine such things.

The following `Filter` plugins are included:

Name                                     | Include\ Path
---------------------------------------- | -------------
[Context](./filters/context.md)          | `pyspelling.filters.context`
[CPP](./filters/cpp.md)                  | `pyspelling.filters.cpp`
[HTML](./filters/html.md)                | `pyspelling.filters.html`
[JavaScript](./filters/javascript.md)    | `pyspelling.filters.javascript`
[Markdown](./filters/markdown.md)        | `pyspelling.filters.markdown`
[Python](./filters/python.md)            | `pyspelling.filters.python`
[Stylesheets](./filters/stylesheets.md)  | `pyspelling.filters.stylesheets`
[Text](./filters/text.md)                | `pyspelling.filters.text`
[URL](./filters/url.md)                  | `pyspelling.filters.url`
[XML](./filters/xml.md)                  | `pyspelling filters.xml`

## Flow Control

`FlowControl` plugins are responsible for controlling the flow of the text down the pipeline. The category of a text chunk is passed to the plugin, and it will return one of three directives:

- `ALLOW`: the chunk(s) of text is allowed to be evaluated by the next filter.
- `SKIP`: the chunk(s) of text should skip the next filter.
- `HALT`: halts the progress of the text chunk(s) down the pipeline and sends it directly to the spell checker.

The following `FlowControl` plugins are included:

Name                                   | Include\ Path
-------------------------------------- | -------------
[Wildcard](./flow_control/wildcard.md) | `pyspelling.flow_control.wildcard`
