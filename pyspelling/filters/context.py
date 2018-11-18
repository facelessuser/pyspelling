"""Text parser."""
from __future__ import unicode_literals
from .. import filters
from .. import util
import codecs
import re
from collections import OrderedDict

DEFAULT_CONTENT = '.*?'


class ContextFilter(filters.Filter):
    """Context filter."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super().__init__(options, default_encoding)

    def get_default_config(self):
        """Get default configuration."""

        return {
            "context_visible_first": False,
            "delimiters": [],
            "escapes": '',
            "normalize_line_endings": True
        }

    def validate_options(self, k, v):
        """Validate options."""

        super().validate_options(k, v)
        if k == 'delimiters':
            for d in v:
                if not isinstance(d, (dict, OrderedDict)):
                    raise ValueError("{}: 'delimters' entries must be of dict type.".format(self.__class__.__name__))
                for key, value in d.items():
                    if key not in ('open', 'close', 'content'):
                        raise KeyError(
                            "{}: '{}' is not a valid key for a 'delimeters' entry.".format(self.__class__.__name__, key)
                        )
                    if not isinstance(value, str):
                        raise ValueError(
                            "{}: 'delimeters' '{}' key should have str values.".format(self.__class__.__name__, value)
                        )

    def setup(self):
        """Setup."""

        self.context_visible_first = self.config['context_visible_first']
        self.delimiters = []
        self.escapes = None
        self.line_endings = self.config['normalize_line_endings']
        escapes = []
        for delimiter in self.config['delimiters']:
            if not isinstance(delimiter, dict):
                continue
            group = util.random_name_gen()
            while (
                group in delimiter['open'] or
                group in delimiter['close'] or
                group in delimiter.get('content', DEFAULT_CONTENT)
            ):
                group = util.random_name_gen()

            pattern = r'%s(?P<%s>%s)(?:%s|\Z)' % (
                delimiter['open'],
                group,
                delimiter.get('content', DEFAULT_CONTENT),
                delimiter['close']
            )
            self.delimiters.append((re.compile(pattern, re.M), group))
        escapes = self.config['escapes']
        if escapes:
            self.escapes = re.compile(escapes)

    def filter(self, source_file, encoding):  # noqa A001
        """Parse file."""

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            text = f.read()

        return [filters.SourceText(self._filter(text), source_file, encoding, 'context')]

    def sfilter(self, source):
        """Filter."""

        return [filters.SourceText(self._filter(source.text), source.context, source.encoding, 'context')]

    def _filter(self, text):
        """Context delimiter filter."""

        if self.line_endings:
            text = self.norm_nl(text)

        new_text = []
        index = 0
        last = 0
        end = len(text)
        while index < end:
            m = self.escapes.match(text, pos=index) if self.escapes else None
            if m:
                index = m.end(0)
                continue
            handled = False
            for delimiter in self.delimiters:
                m = delimiter[0].match(text, pos=index)
                if m:
                    if self.context_visible_first is True:
                        new_text.append(text[last:m.start(0)])
                    else:
                        new_text.append(m.group(delimiter[1]))
                    index = m.end(0)
                    last = index
                    handled = True
                    break
            if handled:
                continue
            index += 1
        if last < end and self.context_visible_first is True:
            new_text.append(text[last:end])

        return ' '.join(new_text)


def get_plugin():
    """Return the filter."""

    return ContextFilter
