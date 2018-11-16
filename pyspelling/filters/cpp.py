"""C++ filter."""
import re
import codecs
from .. import filters
import textwrap

COMMENTS = r'''(?x)
(?P<comments>
    (?P<block>/\*[^*]*\*+(?:[^/*][^*]*\*+)*/) |                 # multi-line comments
    (?P<start>^)?(?P<leading_space>[ \t]*)?(?P<line>//(?:{})*)  # single line comments
) |
(?P<strings>
    {}
    "(?:\\.|[^"\\])*" |                                         # double quotes
    '(?:\\.|[^'\\])*'                                           # single quotes
) |
(?P<code>
    .[^/"'RLuU]*?                                               # everything else
)
'''

CPP_STRING = r'''
(?P<raw>(?:L|u8?|U)?R)"(?P<delim>[^\n ()\t]*)\(.*?\)(?P=delim)" |
(?:L|u8?|U)"(?:\\.|[^"\\])*" |
(?:L|u8?|U)'(?:\\.|[^'\\])*' |
'''

C_COMMENT = re.compile(COMMENTS.format(r'\\.|[^\\\n]+', CPP_STRING), re.DOTALL | re.MULTILINE)

GENERIC = re.compile(COMMENTS.format('[^\n]', ''), re.DOTALL | re.MULTILINE)

TRIGRAPHS = {
    '??=': '#',
    '??/': '\\',
    '??\'': '^',
    '??(': '[',
    '??)': ']',
    '??!': '|',
    '??<': '{',
    '??>': '}',
    '??-': '~'
}

RE_TRIGRAPHS = re.compile(r'\?{2}[=/\'()!<>-]')

BACK_SLASH_TRANSLATION = {
    "\\a": '\a',
    "\\b": '\b',
    "\\f": '\f',
    "\\r": '\r',
    "\\t": '\t',
    "\\n": '\n',
    "\\v": '\v',
    "\\\\": '\\',
    '\\"': '"',
    "\\'": "'",
    "\\?": "?",
    "\\\n": ''
}

RE_ESC = re.compile(
    r'''(?x)
    (?P<special>\\['"abfrtnv?\\\n])|
    (?P<char>\\U[\da-fA-F]{8}|\\u[\da-fA-F]{4}|\\x[\da-fA-F]{1,})|
    (?P<oct>\\[0-7]{1,3})
    '''
)


class CppFilter(filters.Filter):
    """C++ style comment filter."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        self.pattern = GENERIC
        self.trigraphs = False
        super().__init__(options, default_encoding)

    def get_default_config(self):
        """Get default configuration."""

        return {
            "block_comments": True,
            "line_comments": True,
            "group_comments": False,
            "prefix": 'cpp',
            "generic_comments": False,
            "trigraphs": False,
            "strings": False
        }

    def setup(self):
        """Setup."""

        self.blocks = self.config['block_comments']
        self.lines = self.config['line_comments']
        self.group_comments = self.config['group_comments']
        self.prefix = self.config['prefix']
        self.generic_comments = self.config['generic_comments']
        self.strings = self.config['strings']
        self.trigraphs = self.config['trigraphs']
        if not self.generic_comments:
            self.pattern = C_COMMENT

    def evaluate_block(self, groups):
        """Evaluate block comments."""

        if self.blocks:
            self.block_comments.append([groups['block'][2:-2], self.line_num])

    def evaluate_inline_tail(self, groups):
        """Evaluate inline comments at the tail of source code."""

        if self.lines:
            self.line_comments.append([groups['line'][2:].replace('\\\n', ''), self.line_num])

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
                self.line_comments.append([groups['line'][2:].replace('\\\n', ''), self.line_num])
            self.leading = groups['leading_space']
            self.prev_line = self.line_num

    def evaluate_unicode(self, value):
        """Evalute Unicode."""

        if value.startswith('u8'):
            length = 2
            value = value[3:-1]
        elif value.startswith('u'):
            length = 4
            value = value[2:-1]
        else:
            length = 8
            value = value[2:-1]

        def replace_unicode(m):
            """Replace Unicode."""

            groups = m.groupdict()
            esc = m.group(0)
            value = esc
            if groups.get('special'):
                value = BACK_SLASH_TRANSLATION[esc]
            elif groups.get('char'):
                integer = int(esc[2:-1], 16)
                if (
                    (length == 2 and integer <= 0xFF) or
                    (length == 4 and integer <= 0xFFFF) or
                    (length == 8 and integer <= 0x10FFFF)
                ):
                    value = chr(integer)
            elif groups.get('oct'):
                integer = int(esc[1:], 8)
                if (
                    (length == 2 and integer <= 0xFF) or
                    (length == 4 and integer <= 0xFFFF) or
                    (length == 8 and integer <= 0x10FFFF)
                ):
                    value = chr(integer)
            return value

        return self.norm_nl(RE_ESC.sub(replace_unicode, value).replace('\x00', '\n'))

    def evaluate_normal(self, value):
        """Evalute normal string."""

        def replace(m):
            """Replace."""

            groups = m.groupdict()
            esc = m.group(0)
            value = esc
            if groups.get('special'):
                value = BACK_SLASH_TRANSLATION[esc]
            elif groups.get('char') or groups.get('oct'):
                value = ' '
            return value

        return self.norm_nl(RE_ESC.sub(replace_unicode, value).replace('\x00', '\n'))

    def evaluate_strings(self, groups):
        """Evaluate strings."""

        if self.strings:
            if self.generic_comments:
                self.quoted_strings.append([groups['strings'][1:-1], self.line_num])
            else:
                value = groups['strings']
                if groups.get('raw'):
                    olen = len(groups.get('raw')) + len(groups.get('delim')) + 2
                    clen = len(groups.get('delim')) + 2
                    value = self.norm_nl(value[olen:-clen].replace('\x00', '\n'))
                elif not value.startswith(('\'', '"')) and value.endswith('"'):
                    if value.startswith('L'):
                        value = self.evaluate_normal(value[2:-1])
                    else:
                        value = self.evaluate_unicode(value)
                elif value.startswith('"'):
                    value = self.evaluate_normal(value[1:-1])
                else:
                    value = ''

                if value:
                    self.quoted_strings.append([value, self.line_num])

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

    def extend_src_text(self, content, context, text_list, encoding, category):
        """Extend the source text list with the gathered text data."""

        prefix = self.prefix + '-' if self.prefix else ''

        for comment, line in text_list:
            content.append(
                filters.SourceText(
                    textwrap.dedent(comment),
                    "%s (%d)" % (context, line),
                    encoding,
                    prefix + category
                )
            )

    def extend_src(self, content, context, encoding):
        """Extend source list."""

        self.extend_src_text(content, context, self.block_comments, encoding, 'block-comment')
        self.extend_src_text(content, context, self.line_comments, encoding, 'line-comment')
        self.extend_src_text(content, context, self.quoted_strings, 'utf-8', 'strings')

    def process_trigraphs(self, m):
        """Process trigraphs."""

        return TRIGRAPHS[m.group(0)]

    def find_comments(self, text):
        """Find comments."""

        if self.trigraphs:
            text = RE_TRIGRAPHS.sub(self.process_trigraphs, text)

        for m in self.pattern.finditer(self.norm_nl(text)):
            self.evaluate(m)

    def _filter(self, text, context, encoding):
        """Filter JavaScript comments."""

        content = []
        self.line_num = 1
        self.prev_line = -1
        self.leading = ''
        self.block_comments = []
        self.line_comments = []
        self.quoted_strings = []

        self.find_comments(text)
        self.extend_src(content, context, encoding)

        return content

    def filter(self, source_file, encoding):  # noqa A001
        """Parse HTML file."""

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            text = f.read()

        return self._filter(text, source_file, encoding)

    def sfilter(self, source):
        """Filter."""

        return self._filter(source.text, source.context, source.encoding)


def get_plugin():
    """Get filter."""

    return CppFilter
