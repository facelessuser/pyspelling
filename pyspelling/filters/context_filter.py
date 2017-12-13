"""Context filter."""
from .. import filters
import re
from .. import util


class ContextFilter(filters.Filter):
    """Context delimiter class."""

    def __init__(self, options):
        """Initialization."""

        self.context_visible_first = options.get('context_visible_first', False) is True
        self.delimiters = []
        self.escapes = None
        escapes = []
        for delimiter in options.get('delimiters', []):
            if not isinstance(delimiter, dict):
                continue
            group = util.random_name_gen()
            while group in delimiter['open'] or group in delimiter['close']:
                group = util.random_name_gen()
            pattern = r'%s(?P<%s>%s)(?:%s|\Z)' % (delimiter['open'], group, delimiter['content'], delimiter['close'])
            self.delimiters.append((re.compile(pattern, re.M), group))
        escapes = options.get('escapes', None)
        if escapes:
            self.escapes = re.compile(escapes)

    def filter(self, text):
        """Context delimiter filter."""

        new_text = []
        index = 0
        last = 0
        end = len(text)
        while index < end:
            m = self.escapes.match(text, pos=index)
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


def get_filter():
    """Return the filter."""

    return ContextFilter
