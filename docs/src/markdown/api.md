# Plugin API

## Filters

When writing a `Filter` plugin, there are two classes to be aware: `Filter` and `SourceText`. Both classes are found in `pyspelling.filters`.

Each chunk returned by a filter is a `SourceText` object. These objects contain the desired, filtered text from the previous filter along with some metadata: encoding, display context, and a category that describes what kind of text the data is. After all filters have processed the text, each `SourceText`'s content is finally passed to the spell checker.

The text data in a `SourceText` object is always Unicode, but during the filtering process, the filter can decode the Unicode if required as long as it is returned as Unicode at the end of the step.

### `Filter`

`Filter` plugins are subclassed from the `Filter` class.  You'll often want to specify the defaulted value for `default_encoding` in the `__init__`. Simply give it a default value as shown below.

```py3
from .. import filters


class MyFilter(filters.Filter):
    """Spelling Filter."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super().__init__(options, default_encoding)
```

### `Filter.get_default_config`

`get_default_config` is where you should specify your default configuration file. This should contain all accepted options and their default value. All user options that are passed in will override the defaults. If an option is passed in that is not found in the defaults, an error will be raised.

```py3
    def get_default_config(self):
        """Get default configuration."""

        return {
            "enable_something": True,
            "list_of_stuff": ['some', 'stuff']
        }
```

### `Filter.validate_options`

`validate_options` is where you can specify validation of your options. By default, basic validation is done on incoming options. For instance, if you specify a default as a `bool`, the default validator will ensure the passed user options match. Checking is performed on `bool`, `str`, `list`, `dict`, `int`, and `float` types. Nothing beyond simple type checking is performed, so if you had some custom validation, or simply wanted to bypass the default validator with your own, you should override `validate_options`.

```py3
    def validate_options(self, k, v):
        """Validate options."""

        # Call the basic validator
        super().validate_options(k, v)

        # Perform custom validation
        if k == "foo" and v != "bar":
            raise ValueError("Value should be 'bar' for 'foo'")
```

### `Filter.setup`

`setup` is were basic setup can be performed post-validation. At this point, you can access the merged and validated configuration via `self.config`.

```py3
    def setup(self):
        """Setup."""

        self.enable_foo = self.config['foo']
```

### `Filter.reset`

`reset` is called on every new call to the plugin. It allows you to clean up states from previous calls.

```py3
    def reset(self):
        """Reset"""

        self.counter = 0
        self.tracked_stuff = []
```

### `Filter.has_bom`

`has_bom` takes a file stream and is usually used to check the first few bytes. While BOM checking could be performed in `header_check`, this mainly provided as `UTF` BOMs are quite common in many file types, so a specific test was dedicated to it. Additionally, this replaces the old, less flexible `CHECK_BOM` attribute that was deprecated in version `1.2`.

This is useful if you want to handle binary parsing, or a file type that has a custom BOM in the header. When returning encoding in any of the encoding check functions, `None` means no encoding was detecting, an empty string means binary data (encoding validation is skipped), and anything else will be validated and passed through. Just be sure to include a sensible encoding in your `SourceText` object when your plugin returns file content.

```py3
    def has_bom(self, filestream):
        """Check if has BOM."""

        content = filestream.read(2)
        if content == b'PK\x03\x04':
            # Zip file found.
            # Return `BINARY_ENCODE` as content is binary type,
            # but don't return None which means we don't know what we have.
            return filters.BINARY_ENCODE
        # Not a zip file, so pass it on to the normal file checker.
        return super().has_bom(filestream)
```

### `Filter.header_check`

`header_check` is a function that receives the first 1024 characters of the file via `content` that can be scanned for an encoding header. A string with the encoding name should be returned or `None` if a valid encoding header cannot be found.

```py3
    def header_check(self, content):
        """Special encode check."""

        return None
```

### `Filter.content_check`

`content_check` receives a file object which allows you to check the entire file buffer to determine encoding. A string with the encoding name should be returned or `None` if a valid encoding header cannot be found.

```py3
    def content_check(self, filestream):
        """File content check."""

        return None
```

### `Filter.filter`

`filter` is called when the `Filter` object is the first in the chain. This means the file has not been read from disk yet, so we must handle opening the file before applying the filter and then return a list of `SourceText` objects. The first filter in the chain is handled differently in order to give the opportunity to handle files that require more complex methods to acquire the Unicode strings. You can read the file in binary format or directly to Unicode.  You can run parsers or anything else you need in order to get the required Unicode text for the `SourceText` objects. You can create as many `SourceText` objects as you desired and assign them categories so that other `Filter` objects can avoid them if desired. Below is the default which reads the entire file into a single object providing the file name as the context, the encoding, and the category `text`.

```py3
    def filter(self, source_file, encoding):  # noqa A001
        """Open and filter the file from disk."""

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            text = f.read()
        return [SourceText(text, source_file, encoding, 'text')]
```

### `Filter.sfilter`

`sfilter` is called for all `Filter` objects following the first.  The function is passed a `SourceText` object from which the text, context, encoding can all be extracted. Here you can manipulate the text back to bytes if needed, wrap the text in an `io.StreamIO` object to act as a file stream, run parsers, or anything you need to manipulate the buffer to filter the Unicode text for the `SourceText` objects.

```py3
    def sfilter(self, source):
        """Execute filter."""

        return [SourceText(source.text, source.context, source.encoding, 'text')]
```

If a filter only works either as the first in the chain, or only as a secondary filter in the chain, you could raise an exception if needed.  In most cases, you should be able to have an appropriate `filter` and `sfilter`, but there are most likely cases (particular when dealing with binary data) where only a `filter` method could be provided.

Check out the default filter plugins provided with the source to see real world examples.

### `get_plugin`

And don't forget to provide a function in the file called `get_plugin`! `get_plugin` is the entry point and should return your `Filter` object.

```py3
def get_plugin():
    """Return the filter."""

    return HtmlFilter
```

### `SourceText`

As previously mentioned, filters must return a list of `SourceText` objects.

```py3
class SourceText(namedtuple('SourceText', ['text', 'context', 'encoding', 'category', 'error'])):
    """Source text."""
```

Each object should contain a Unicode string (`text`), some context on the given text hunk (`context`), the encoding which the Unicode text was originally in (`encoding`), and a `category` that is used to omit certain hunks from other filters in the chain (`category`). `SourceText` should not contain byte strings, and if they do, they will not be passed to additional filters. `error` is optional and is only provided message when something goes wrong.

When receiving a `SourceText` object in your plugin, you can access the the content via attributes with the same name as the parameters above:

```pycon3
>>> source.text
'Some Text'
>>> source.context
'foo.txt'
>>> source.encoding
'utf-8'
>>> source.category
'some-category'
```

Be mindful when adjusting the context in subsequent items in the pipeline chain. Generally you should only append additional context so as not to wipe out previous contextual data. It may not always make sense to append additional data, so some filters might just pass the previous context as the new context.

If you have a particular chunk of text that has a problem, you can return an error in the `SourceText` object.  Errors really only need a context and the error as they won't be passed to the spell checker or to any subsequent steps in the pipeline. Errors are only used to alert the user that something went wrong. `SourceText` objects with errors will not be passed down the chain and will not be passed to the spell checker.

```py3
if error:
    content = [SourceText('', source_file, '', '', error)]
```

## Flow Control

`FlowControl` plugins are simple plugins that take the category from a `SourceText` object, and simply returns either the directive `HALT`, `SKIP`, or `ALLOW`. This controls whether the associated `SourceText` object's progress is halted in the pipeline, skips the next filter, or is explicitly allowed in the next filter. The directives and `FlowControl` class are found in `pyspelling.flow_control`.

### `FlowControl`

`FlowControl` plugins should be subclassed from `FlowControl`. If you need to you can override the `__init__`, but remember to call the original with `super` to ensure options are handled.

```py3
class MyFlowControl(flow_control.FlowControl):
    """Flow control plugin."""

    def __init__(self, config):
        """Initialization."""

        super().__init__(config)
```

### `FlowControl.get_default_config`

`get_default_config` is where you should specify your default configuration file. This should contain all accepted options and their default value. All user options that are passed in will override the defaults. If an option is passed in that is not found in the defaults, an error will be raised.

```py3
    def get_default_config(self):
        """Get default configuration."""

        return {
            "enable_something": True,
            "list_of_stuff": ['some', 'stuff']
        }
```

### `FlowControl.validate_options`

`validate_options` is where you can specify validation of your options. By default, basic validation is done on incoming options. For instance, if you specify a default as a `bool`, the default validator will ensure the passed user options match. Checking is performed on `bool`, `str`, `list`, `dict`, `int`, and `float` types. Nothing beyond simple type checking is performed, so if you had some custom validation, or simply wanted to bypass the default validator with your own, you should override `validate_options`.

```py3
    def validate_options(self, k, v):
        """Validate options."""

        # Call the basic validator
        super().validate_options(k, v)

        # Perform custom validation
        if k == "foo" and v != "bar":
            raise ValueError("Value should be 'bar' for 'foo'")
```

### `FlowControl.setup`

`setup` is were basic setup can be performed post-validation. At this point, you can access the merged and validated configuration via `self.config`.

```py3
    def setup(self):
        """Setup."""

        self.enable_foo = self.config['foo']
```

### `FlowControl.reset`

`reset` is called on every new call to the plugin. It allows you to clean up states from previous calls.

```py3
    def reset(self):
        """Reset"""

        self.counter = 0
        self.tracked_stuff = []
```

### `FlowControl.adjust_flow`

After handling the options, there is only one other function available for overrides: `adjust_flow`.  Adjust flow receives the category from the `SourceText` being passed down the pipeline. Here the decision is made to as to what must be done with the object. Simply return `HALT`, `SKIP`, or `ALLOW` to control the flow for that `SourceText` object.

```py3
    def adjust_flow(self, category):
        """Adjust the flow of source control objects."""

        status = flow_control.SKIP
        for allow in self.allow:
            if fnmatch.fnmatch(category, allow, flags=self.FNMATCH_FLAGS):
                status = flow_control.ALLOW
                for skip in self.skip:
                    if fnmatch.fnmatch(category, skip, flags=self.FNMATCH_FLAGS):
                        status = flow_control.SKIP
                for halt in self.halt:
                    if fnmatch.fnmatch(category, halt, flags=self.FNMATCH_FLAGS):
                        status = flow_control.HALT
                if status != flow_control.ALLOW:
                    break
        return status
```

Check out the default flow control plugins provided with the source to see real world examples.

### `get_plugin`

And don't forget to provide a function in the file called `get_plugin`! `get_plugin` is the entry point and should return your `FlowControl` object.

```py3
def get_plugin():
    """Get flow controller."""

    return WildcardFlowControl
```
