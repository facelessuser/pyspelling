"""C++ filter."""
import re
import codecs
from .. import filters
import textwrap

RE_COMMENT = re.compile(
    r'''(?x)
        (?P<comments>
            (?P<block>/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)                        # multi-line comments
          | (?P<start>^)?(?P<leading_space>[ \t]*)?(?P<line>//(?:[^\r\n])*)  # single line comments
        )
      | (?P<code>
            "(?:\\.|[^"\\])*"                                                # double quotes
            '(?:\\.|[^'\\])*'                                                # single quotes
          | .[^/"']*?                                                        # everything else
        )
    ''',
    re.DOTALL | re.MULTILINE
)


class CppFilter(filters.Filter):
    """C++ style comment filter."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        self.blocks = options.get('block_comments', True) is True
        self.lines = options.get('line_comments', True) is True
        self.group_comments = options.get('group_comments', False) is True
        self.prefix = options.get('prefix', 'cpp')
        super(CppFilter, self).__init__(options, default_encoding)

    def evaluate_block(self, groups):
        """Evaluate block comments."""

        if self.blocks:
            self.block_comments.append([groups['block'][2:-2], self.line_num])

    def evaluate_inline_tail(self, groups):
        """Evaluate inline comments at the tail of source code."""

        if self.lines:
            self.line_comments.append([groups['line'][2:], self.line_num])

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
                self.line_comments[-1][0] += '\n' + groups['line'][2:]
            else:
                self.line_comments.append([groups['line'][2:], self.line_num])
            self.leading = groups['leading_space']
            self.prev_line = self.line_num

    def _evaluate(self, m):
        """Search for comments."""

        g = m.groupdict()
        if g["code"]:
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

    def find_comments(self, text):
        """Find comments."""

        for m in RE_COMMENT.finditer(text):
            self._evaluate(m)

    def _filter(self, text, context, encoding):
        """Filter JavaScript comments."""

        content = []
        self.line_num = 1
        self.prev_line = -1
        self.leading = ''
        self.block_comments = []
        self.line_comments = []

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
