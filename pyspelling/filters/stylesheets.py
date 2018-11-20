"""Stylesheets filter."""
import re
import codecs
import textwrap
from .. import filters

TARGETS = r'''(?x)
(?P<comments>
    (?P<block>/\*[^*]*\*+(?:[^/*][^*]*\*+)*/) # multi-line comments
    {}
) |
(?P<strings>
    "(?:\\.|[^"\\\n])*" |                     # double quotes
    '(?:\\.|[^'\\\n])*'                       # single quotes
) |
(?P<code>
    .[^/"' \t\n]*?                            # everything else
)
'''

INLINE_COMMENTS = r'| (?P<start>^)?(?P<leading_space>[ \t]*)?(?P<line>//(?:[^\n])*)'

RE_CSS = re.compile(TARGETS.format(''), re.DOTALL | re.MULTILINE)
RE_SCSS = re.compile(TARGETS.format(INLINE_COMMENTS), re.DOTALL | re.MULTILINE)

CSS = 0
SASS = 1
SCSS = 2

STYLESHEET_TYPE = {
    "css": CSS,
    "sass": SASS,
    "scss": SCSS
}


class StylesheetsFilter(filters.Filter):
    """Stylesheets filter."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super().__init__(options, default_encoding)

    def get_default_config(self):
        """Get default configuration."""

        return {
            "block_comments": True,
            "line_comments": True,
            "group_comments": False,
            "stylesheets": 'css'
        }

    def validate_options(self, k, v):
        """Validate options."""

        super().validate_options(k, v)
        if k == 'stylesheets' and v not in STYLESHEET_TYPE:
            raise ValueError("{}: '{}' is not a valid value for '{}'".format(self.__class__.__name, v, k))

    def setup(self):
        """Setup."""

        self.blocks = self.config['block_comments']
        self.lines = self.config['line_comments']
        self.group_comments = self.config['group_comments']
        # If the style isn't found, just go with CSS, then use the appropriate prefix.
        self.stylesheets = STYLESHEET_TYPE.get(self.config['stylesheets'].lower(), CSS)
        self.prefix = [k for k, v in STYLESHEET_TYPE.items() if v == SASS][0]
        self.pattern = RE_CSS if self.stylesheets == CSS else RE_SCSS

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

    def evaluate(self, m):
        """Search for comments."""

        g = m.groupdict()
        if g["strings"]:
            self.line_num += g['strings'].count('\n')
        elif g["code"]:
            self.line_num += g["code"].count('\n')
        else:
            if g['block']:
                self.evaluate_block(g)
            elif self.stylesheets != CSS:
                if g['start'] is None:
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

    def find_content(self, text):
        """Find content."""

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

        self.find_content(text)
        self.extend_src(content, context)

        return content

    def filter(self, source_file, encoding):  # noqa A001
        """Parse stylesheet file."""

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            text = f.read()

        return self._filter(text, source_file, encoding)

    def sfilter(self, source):
        """Filter."""

        return self._filter(source.text, source.context, source.encoding)


def get_plugin():
    """Get filter."""

    return StylesheetsFilter
