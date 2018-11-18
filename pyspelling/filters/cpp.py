"""C++ filter."""
import re
import codecs
from .. import filters
import textwrap
import struct
import sys

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
    .[^/"'{}]*?                                               # everything else
)
'''

CPP_STRING = r'''
(?P<raw>(?:L|u8?|U)?R)"(?P<delim>[^\n ()\t]*)\(.*?\)(?P=delim)" |
(?:L|u8?|U)"(?:\\.|[^"\\])*" |
(?:L|u8?|U)'(?:\\.|[^'\\])*' |
'''

C_COMMENT = re.compile(COMMENTS.format(r'\\.|[^\\\n]+', CPP_STRING, 'RLuU'), re.DOTALL | re.MULTILINE)

GENERIC = re.compile(COMMENTS.format('[^\n]', '', ''), re.DOTALL | re.MULTILINE)

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

RE_UESC = re.compile(
    r'''(?x)
    (?P<special>\\['"abfrtnv?\\\n])|
    (?P<char>\\U[\da-fA-F]{8}|\\u[\da-fA-F]{4}|\\x[\da-fA-F]{1,})|
    (?P<oct>\\[0-7]{1,3})
    '''
)

RE_ESC = re.compile(
    r'''(?x)
    (?P<special>\\['"abfrtnv?\\\n])|
    (?P<char>\\U[\da-fA-F]{8}|\\u[\da-fA-F]{4}|(?:\\x[\da-fA-F]{1,})+)|
    (?P<oct>(?:\\[0-7]{1,3})+)
    '''
)

BIT8 = 1
BIT16 = 2
BIT32 = 4

BIG_ENDIAN = 0x10
LITTLE_ENDIAN = 0x20
CURRENT_ENDIAN = BIG_ENDIAN if sys.byteorder == 'big' else LITTLE_ENDIAN

BYTE_STORE = {
    (BIT8 | BIG_ENDIAN): '>B',
    (BIT16 | BIG_ENDIAN): '>H',
    (BIT32 | BIG_ENDIAN): '>I',
    (BIT8 | LITTLE_ENDIAN): '<B',
    (BIT16 | LITTLE_ENDIAN): '<H',
    (BIT32 | LITTLE_ENDIAN): '<I'
}


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
            "generic_mode": False,
            "trigraphs": False,
            "strings": False,
            "decode_escapes": True,
            "exec_charset": 'utf-8',
            "wide_exec_charset": 'utf-32',
            "charset_size": 1,
            "wide_charset_size": 4,
            "allowed": "suw"
        }

    def validate_options(self, k, v):
        """Validate options."""

        super().validate_options(k, v)
        if k == 'charset_size':
            if v not in (1, 2, 4):
                raise ValueError("{}: '{}' is an unsupported charset size".format(self.__class__.__name__, v))
        elif k == 'wide_charset_size':
            if v not in (2, 4):
                raise ValueError("{}: '{}' is an unsupported wide charset size".format(self.__class__.__name__, v))
        elif k in ('exec_charset', 'wide_exec_charset'):
            # See if parsing fails.
            self.get_encoding_name(v)
        elif k == 'allowed':
            for c in v.lower():
                if c not in 'rsuw':
                    raise ValueError("{}: '{}' is not a valid string type".format(self.__class__.__name__, c))

    def eval_string_type(self, stype):
        """Evaluate string type."""

        return set([c for c in stype.lower()])

    def get_encoding_name(self, name):
        """Get encoding name."""

        name = codecs.lookup(
            filters.PYTHON_ENCODING_NAMES.get(name, name).lower()
        ).name

        if name.startswith(('utf-32', 'utf-16')):
            name = name[:6]
            if CURRENT_ENDIAN == BIG_ENDIAN:
                name += '-be'
            else:
                name += '-le'

        if name == 'utf-8-sig':
            name = 'utf-8'
        return name

    def setup(self):
        """Setup."""

        self.blocks = self.config['block_comments']
        self.lines = self.config['line_comments']
        self.group_comments = self.config['group_comments']
        self.prefix = self.config['prefix']
        self.generic_mode = self.config['generic_mode']
        self.strings = self.config['strings']
        self.trigraphs = self.config['trigraphs']
        self.decode_escapes = self.config['decode_escapes']
        self.charset_size = self.config['charset_size']
        self.wide_charset_size = self.config['wide_charset_size']
        self.exec_charset = self.get_encoding_name(self.config['exec_charset'])
        self.wide_exec_charset = self.get_encoding_name(self.config['wide_exec_charset'])
        self.allowed = self.eval_string_type(self.config['allowed'])
        if not self.generic_mode:
            self.pattern = C_COMMENT

    def evaluate_block(self, groups):
        """Evaluate block comments."""

        if self.blocks:
            self.block_comments.append([groups['block'][2:-2], self.line_num, self.current_encoding])

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

    def evaluate_unicode(self, value):
        """Evaluate Unicode."""

        if value.startswith('u8'):
            length = 1
            value = value[3:-1]
        elif value.startswith('u'):
            length = 2
            value = value[2:-1]
        else:
            length = 4
            value = value[2:-1]

        def replace_unicode(m):
            """Replace Unicode."""

            groups = m.groupdict()
            esc = m.group(0)
            value = esc
            if groups.get('special'):
                # Handle basic string escapes.
                value = BACK_SLASH_TRANSLATION[esc]
            elif groups.get('char') or groups.get('oct'):
                # Handle character escapes.
                integer = int(esc[2:], 16) if groups.get('char') else int(esc[1:], 8)
                if (
                    (length < 2 and integer <= 0xFF) or
                    (length < 4 and integer <= 0xFFFF) or
                    (length >= 4 and integer <= 0x10FFFF)
                ):
                    try:
                        value = chr(integer)
                    except Exception:
                        value = ' '
            return value

        return self.norm_nl(RE_UESC.sub(replace_unicode, value).replace('\x00', '\n')), 'utf-8'

    def evaluate_normal(self, value):
        """Evaluate normal string."""

        if value.startswith('L'):
            size = self.wide_charset_size
            encoding = self.wide_exec_charset
            value = value[2:-1]
            pack = BYTE_STORE[size | CURRENT_ENDIAN]
        else:
            size = self.charset_size
            encoding = self.exec_charset
            value = value[1:-1]
            pack = BYTE_STORE[size | CURRENT_ENDIAN]
        max_value = 2 ** (size * 8) - 1

        def replace(m):
            """Replace."""

            groups = m.groupdict()
            esc = m.group(0)
            value = esc
            if groups.get('special'):
                # Handle basic string escapes.
                value = BACK_SLASH_TRANSLATION[esc]
            elif groups.get('char'):
                # Handle hex/Unicode character escapes
                if value.startswith('\\x'):
                    values = [int(x, 16) for x in value[2:].split('\\x')]
                    for i, v in enumerate(values):
                        if v <= max_value:
                            values[i] = struct.pack(pack, v)
                        else:
                            values[i] = b' '
                    value = b''.join(values).decode(encoding, errors='replace')
                else:
                    integer = int(value[2:], 16)
                    value = chr(integer).encode(encoding, errors='replace').decode(encoding)
            elif groups.get('oct'):
                # Handle octal escapes.
                values = [int(x, 8) for x in value[1:].split('\\')]
                for i, v in enumerate(values):
                    if v <= max_value:
                        values[i] = struct.pack(pack, v)
                    else:
                        values[i] = b' '
                value = b''.join(values).decode(encoding, errors='replace')
            return value

        text = self.norm_nl(RE_ESC.sub(replace, value)).replace('\x00', '\n')
        if encoding.startswith(('utf-32', 'utf-16')):
            encoding = 'utf-8'
        return text, encoding

    def evaluate_strings(self, groups):
        """Evaluate strings."""

        if self.strings:
            encoding = self.current_encoding
            if self.generic_mode:
                # Generic assumes no escapes rules.
                self.quoted_strings.append([groups['strings'][1:-1], self.line_num, encoding])
            else:
                value = groups['strings']
                if groups.get('raw'):
                    start = groups.get('raw')[0].lower()
                    if (
                        'r' not in self.allowed or
                        (start == 'r' and 's' not in self.allowed) or
                        (start == 'l' and 'w' not in self.allowed) or
                        (start == 'u' and 'u' not in self.allowed)
                    ):
                        value = ''
                    else:
                        # Handle raw strings. We can handle even if decoding is disabled.
                        olen = len(groups.get('raw')) + len(groups.get('delim')) + 2
                        clen = len(groups.get('delim')) + 2
                        value = self.norm_nl(value[olen:-clen].replace('\x00', '\n'))
                elif (
                    self.decode_escapes and not value.startswith(('\'', '"')) and
                    not value.startswith('L') and value.endswith('"')
                ):
                    if 'u' not in self.allowed:
                        value = ''
                    else:
                        # Decode Unicode string. May have added unsupported chars, so use `UTF-8`.
                        value, encoding = self.evaluate_unicode(value)
                elif self.decode_escapes and value.startswith(('"', 'L')):
                    start = value[0]
                    if (start == 'L' and 'w' not in self.allowed) or (start != 'L' and 's' not in self.allowed):
                        value = ''
                    else:
                        # Decode normal strings.
                        value, encoding = self.evaluate_normal(value)
                elif not self.decode_escapes and value.endswith('"'):
                    # Don't decode and just return string content.
                    value = self.norm_nl(value[value.index('"') + 1:-1]).replace('\x00', '\n')
                else:
                    # Char constant. Just ignore
                    value = ''

                if value:
                    self.quoted_strings.append([value, self.line_num, encoding])

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
        self.extend_src_text(content, context, self.quoted_strings, 'string')

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
