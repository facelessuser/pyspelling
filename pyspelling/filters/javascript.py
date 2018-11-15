"""JavaScript filter."""
import re
from . import cpp

RE_JSDOC = re.compile(r"(?s)^/\*\*$(.*?)[ \t]*\*/", re.MULTILINE)

BACK_SLASH_TRANSLATION = {
    "\\b": '\b',
    "\\f": '\f',
    "\\r": '\r',
    "\\t": '\t',
    "\\n": '\n',
    "\\v": '\v',
    "\\\\": '\\',
    '\\"': '"',
    "\\'": "'",
    "\\\n": '',
    "\\0": "\000"
}

RE_ESC = re.compile(
    r'''(?x)
    (?P<oct>\\(?:[1-7][0-7]{0,2}|[0-7]{2,3}))|
    (?P<special>\\['"bfrt0nv\\\n])|
    (?P<char>\\u(?:\{[\da-fA-F]+\}|[\da-fA-F]{4})|\\x[\da-fA-F]{2}) |
    (?P<other>\\.)
    '''
)

RE_SURROGATES = re.compile(r'([\ud800-\udbff])([\udc00-\udfff])')


class JavaScriptFilter(cpp.CppFilter):
    """JavaScript filter."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super().__init__(options, default_encoding)

    def get_default_config(self):
        """Get default configuration."""

        return {
            "block_comments": True,
            "line_comments": True,
            "group_comments": False,
            "decode_escapes": True,
            "strings": False,
            "jsdocs": False
        }

    def setup(self):
        """Setup."""

        self.blocks = self.config['block_comments']
        self.lines = self.config['line_comments']
        self.group_comments = self.config['group_comments']
        self.jsdocs = self.config['jsdocs']
        self.decode_escapes = self.config['decode_escapes']
        self.strings = self.config['strings']
        self.prefix = 'js'

    def replace_escapes(self, m):
        """Replace escapes."""

        groups = m.groupdict()
        esc = m.group(0)
        if groups.get('special'):
            value = BACK_SLASH_TRANSLATION[esc]
        elif groups.get('char'):
            try:
                if esc.endswith('}'):
                    value = chr(int(esc[3:-1], 16))
                else:
                    value = chr(int(esc[2:], 16))
            except Exception:
                value = esc
        elif groups.get('oct'):
            # JavaScript only supports hex range.
            # So \400 would be \40 + '0'
            value = int(esc[1:], 8)
            overflow = ''
            if value > 255:
                value = esc[1:-1]
                overflow + esc[-1]
            value = chr(value) + overflow
        elif('other'):
            value = esc[1:]
        return value

    def replace_surrogates(self, m):
        """Replace surrogates."""

        high, low = ord(m.group(1)), ord(m.group(2))
        return chr((high - 0xD800) * 0x400 + low - 0xDC00 + 0x10000)

    def evaluate_strings(self, groups):
        """Evaluate strings."""

        if self.strings:
            if self.decode_escapes:
                value = RE_SURROGATES.sub(
                    self.replace_surrogates,
                    RE_ESC.sub(self.replace_escapes, groups['strings'][1:-1])
                )
            else:
                value = groups['strings'][1:-1]
            self.quoted_strings.append([value, self.line_num])

    def evaluate_block(self, groups):
        """Evaluate block comments."""

        if self.jsdocs:
            m1 = RE_JSDOC.match(groups['comments'])
            if m1:
                lines = []
                for line in m1.group(1).splitlines(True):
                    l = line.lstrip()
                    lines.append(l[1:] if l.startswith('*') else l)
                self.jsdoc_comments.append([''.join(lines), self.line_num])
            elif self.blocks:
                self.block_comments.append([groups['block'][2:-2], self.line_num])
        elif self.blocks:
            self.block_comments.append([groups['block'][2:-2], self.line_num])

    def extend_src(self, content, context, encoding):
        """Extend source list."""

        self.extend_src_text(content, context, self.block_comments, encoding, 'block-comment')
        self.extend_src_text(content, context, self.line_comments, encoding, 'line-comment')
        self.extend_src_text(content, context, self.jsdoc_comments, encoding, 'docs')
        self.extend_src_text(content, context, self.quoted_strings, encoding, 'strings')

    def _filter(self, text, context, encoding):
        """Filter JavaScript comments."""

        self.jsdoc_comments = []
        return super()._filter(text, context, encoding)


def get_plugin():
    """Get filter."""

    return JavaScriptFilter
