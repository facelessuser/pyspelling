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
    "(?:\\.|[^"\\])*" |                                         # double quotes
    '(?:\\.|[^'\\])*'                                           # single quotes
) |
(?P<code>
    .[^/"']*?                                                   # everything else
)
'''

C_COMMENT = re.compile(COMMENTS.format(r'\\.|[^\\\n]+'), re.DOTALL | re.MULTILINE)

GENERIC = re.compile(COMMENTS.format('[^\n]'), re.DOTALL | re.MULTILINE)

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
            "trigraphs": False
        }

    def setup(self):
        """Setup."""

        self.blocks = self.config['block_comments']
        self.lines = self.config['line_comments']
        self.group_comments = self.config['group_comments']
        self.prefix = self.config['prefix']
        self.generic_comments = self.config['generic_comments']
        self.enable_strings = False
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
            self.line_comments.append([groups['line'][2:].replace('\n', ''), self.line_num])

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
                self.line_comments[-1][0] += '\n' + groups['line'][2:].replace('\n', '')
            else:
                self.line_comments.append([groups['line'][2:].replace('\n', ''), self.line_num])
            self.leading = groups['leading_space']
            self.prev_line = self.line_num

    def evaluate_strings(self, groups):
        """Evaluate strings."""

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
        if self.strings:
            self.extend_src_text(content, context, self.strings, encoding, 'strings')

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
        self.strings = []

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
