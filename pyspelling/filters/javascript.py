"""JavaScript filter."""
import re
import textwrap
import codecs
from .. import filters

RE_JSDOC = re.compile(r"(?s)^/\*\*$(.*?)[ \t]*\*/", re.MULTILINE)

COMMENTS = r'''(?x)
(?P<comments>
    (?P<block>/\*[^*]*\*+(?:[^/*][^*]*\*+)*/) |                 # multi-line comments
    (?P<start>^)?(?P<leading_space>[ \t]*)?(?P<line>//(?:[^\n])*)  # single line comments
) |
(?P<strings>
    "(?:\\.|[^"\\])*" |                                         # double quotes
    '(?:\\.|[^'\\])*'                                           # single quotes
) |
(?P<code>
    .[^/"']*?                                               # everything else
)
'''

GENERIC = re.compile(COMMENTS, re.DOTALL | re.MULTILINE)

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


class JavaScriptFilter(filters.Filter):
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

        self.pattern = GENERIC
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
        return value.replace('\x00', '\n')

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
            self.quoted_strings.append([value, self.line_num, 'utf-8'])

    def evaluate_inline_tail(self, groups):
        """Evaluate inline comments at the tail of source code."""

        if self.lines:
            self.line_comments.append([groups['line'][2:].replace('\\\n', ''), self.line_num, self.current_encoding])

    def evaluate_inline(self, groups):
        """Evaluate inline comments on their own lines."""

        # Consecutive lines with only comments with same leading whitespace
        # will be captured as a single block.
        if self.lines:
            if (
                self.group_comments and
                self.line_num == self.prev_line + 1 and
                groups['leading_space'] == self.leading
            ):
                self.line_comments[-1][0] += '\n' + groups['line'][2:].replace('\\\n', '')
            else:
                self.line_comments.append(
                    [groups['line'][2:].replace('\\\n', ''), self.line_num, self.current_encoding]
                )
            self.leading = groups['leading_space']
            self.prev_line = self.line_num

    def evaluate_block(self, groups):
        """Evaluate block comments."""

        if self.jsdocs:
            m1 = RE_JSDOC.match(groups['comments'])
            if m1:
                lines = []
                for line in m1.group(1).splitlines(True):
                    l = line.lstrip()
                    lines.append(l[1:] if l.startswith('*') else l)
                self.jsdoc_comments.append([''.join(lines), self.line_num, self.current_encoding])
            elif self.blocks:
                self.block_comments.append([groups['block'][2:-2], self.line_num, self.current_encoding])
        elif self.blocks:
            self.block_comments.append([groups['block'][2:-2], self.line_num, self.current_encoding])

    def evaluate(self, m):
        """Search for comments."""

        g = m.groupdict()
        if g["strings"]:
            self.evaluate_strings(g)
            self.line_num += g['strings'].count('\n')
        elif g["code"]:
            self.line_num += g["code"].count('\n')
        else:
            if g['block']:
                self.evaluate_block(g)
            elif g['start'] is None:
                self.evaluate_inline_tail(g)
            else:
                self.evaluate_inline(g)
            self.line_num += g['comments'].count('\n')

    def extend_src_text(self, content, context, text_list, category):
        """Extend the source text list with the gathered text data."""

        prefix = self.prefix + '-' if self.prefix else ''

        for comment, line, encoding in text_list:
            content.append(
                filters.SourceText(
                    textwrap.dedent(comment),
                    "%s (%d)" % (context, line),
                    encoding,
                    prefix + category
                )
            )

    def extend_src(self, content, context):
        """Extend source list."""

        self.extend_src_text(content, context, self.block_comments, 'block-comment')
        self.extend_src_text(content, context, self.line_comments, 'line-comment')
        self.extend_src_text(content, context, self.jsdoc_comments, 'docs')
        self.extend_src_text(content, context, self.quoted_strings, 'strings')

    def find_comments(self, text):
        """Find comments."""

        for m in self.pattern.finditer(self.norm_nl(text)):
            self.evaluate(m)

    def _filter(self, text, context, encoding):
        """Filter JavaScript comments."""

        content = []
        self.jsdoc_comments = []
        self.current_encoding = encoding
        self.line_num = 1
        self.prev_line = -1
        self.leading = ''
        self.block_comments = []
        self.line_comments = []
        self.quoted_strings = []

        self.find_comments(text)
        self.extend_src(content, context)

        return content

    def filter(self, source_file, encoding):  # noqa A001
        """Parse JavaScript file."""

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            text = f.read()

        return self._filter(text, source_file, encoding)

    def sfilter(self, source):
        """Filter."""

        return self._filter(source.text, source.context, source.encoding)


def get_plugin():
    """Get filter."""

    return JavaScriptFilter
