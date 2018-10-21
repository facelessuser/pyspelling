"""Text parser."""
from __future__ import unicode_literals
from .. import filters
from .. import util
import codecs
import re

DEFAULT_CONTENT = '.*?'


class ContextFilter(filters.Filter):
    """Context filter."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        self.context_visible_first = options.get('context_visible_first', False) is True
        self.delimiters = []
        self.escapes = None
        escapes = []
        for delimiter in options.get('delimiters', []):
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
        escapes = options.get('escapes', None)
        if escapes:
            self.escapes = re.compile(escapes)

        super(ContextFilter, self).__init__(options, default_encoding)

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
