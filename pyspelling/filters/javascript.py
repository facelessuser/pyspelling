"""JavaScript filter."""
import re
import textwrap
import codecs
from .. import filters

RE_JSDOC = re.compile(r"(?s)^/\*\*$(.*?)[ \t]*\*/", re.MULTILINE)

RE_BLOCK_COMMENT = re.compile(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/', re.DOTALL | re.MULTILINE)
RE_COMMENT = re.compile(r'(?P<start>^)?(?P<leading_space>[ \t]*)?(?P<line>//(?:[^\n])*)', re.DOTALL | re.MULTILINE)
RE_STRING = re.compile(r'''"(?:\\.|[^"\\\n])*"|(?:\\.|[^'\\\n])*''', re.DOTALL | re.MULTILINE)
RE_TEMPLATE_START = re.compile(r'`((?:\\.|\$(?!\{)|[^`\\$])*)(`|\$\{)', re.DOTALL | re.MULTILINE)
RE_TEMPLATE_MIDDLE_END = re.compile(r'((?:\\.|\$(?!\{)|[^`\\$])*)(`|\$\{)', re.DOTALL | re.MULTILINE)

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
    "\\`": "`",
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

RE_TEMP_ESC = re.compile(
    r'''(?x)
    (?P<special>\\['"`bfrt0nv\\\n])|
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

    def evaluate_strings(self, string, temp=False):
        """Evaluate strings."""

        value = ''
        if self.strings:
            if self.decode_escapes:
                value = RE_SURROGATES.sub(
                    self.replace_surrogates,
                    (RE_TEMP_ESC if temp else RE_ESC).sub(self.replace_escapes, string)
                )
            else:
                value = string
            if not temp:
                self.quoted_strings.append([value, self.line_num, 'utf-8'])
        return value

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

    def evaluate_block(self, comments):
        """Evaluate block comments."""

        if self.jsdocs:
            m1 = RE_JSDOC.match(comments)
            if m1:
                lines = []
                for line in m1.group(1).splitlines(True):
                    l = line.lstrip()
                    lines.append(l[1:] if l.startswith('*') else l)
                self.jsdoc_comments.append([''.join(lines), self.line_num, self.current_encoding])
            elif self.blocks:
                self.block_comments.append([comments[2:-2], self.line_num, self.current_encoding])
        elif self.blocks:
            self.block_comments.append([comments[2:-2], self.line_num, self.current_encoding])

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

    def find_content(self, text, index=0, backtick=False):
        """Find content."""

        curly_count = 0
        last = '\n'
        self.lines_num = 1
        length = len(text)
        while index < length:
            start_index = index
            c = text[index]
            if c == '{' and backtick:
                curly_count += 1
            elif c == '}' and backtick:
                if curly_count:
                    curly_count -= 1
                else:
                    index += 1
                    return index
            elif c == '`':
                done = False
                first = True
                backtick_content = []
                start_index = index
                while not done:
                    m = (RE_TEMPLATE_START if first else RE_TEMPLATE_MIDDLE_END).match(text, index)
                    first = False
                    if m:
                        self.line_num += m.group(0).count('\n')
                        content = self.evaluate_strings(m.group(1), True)
                        if content:
                            backtick_content.append(content)
                        index = m.end(0)
                        if m.group(2) == '${':
                            index = self.find_content(text, index, True)
                        else:
                            done = True
                    else:
                        done = True
                if backtick_content:
                    self.quoted_strings.append([' '.join(backtick_content), self.line_num, 'utf-8'])
            elif c in ('\'', '"'):
                m = RE_STRING.match(text, index)
                if m:
                    self.evaluate_strings(m.group(0)[1:-1])
                    self.line_num += m.group(0).count('\n')
                    index = m.end(0)
            elif c == '\n':
                self.line_num += 1
            elif last == '\n' or c == '/':
                m = RE_COMMENT.match(text, index)
                if m:
                    g = m.groupdict()
                    if g['start'] is None:
                        self.evaluate_inline_tail(g)
                    else:
                        self.evaluate_inline(g)
                    index = m.end(0)
                elif c == '/':
                    m = RE_BLOCK_COMMENT.match(text, index)
                    if m:
                        self.evaluate_block(m.group(0))
                        self.line_num += m.group(0).count('\n')
                        index = m.end(0)

            if index == start_index:
                index += 1
            last = text[index - 1]

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

        self.find_content(self.norm_nl(text))
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
