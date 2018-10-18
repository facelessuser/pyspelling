"""
Python filter.

Parse Python docstrings.
"""
from __future__ import unicode_literals
from .. import filters
import re
import textwrap
import tokenize
import codecs
import io

tokenizer = tokenize.generate_tokens
PREV_DOC_TOKENS = (tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE, tokenize.ENCODING)

RE_PY_ENCODE = re.compile(
    br'^[^\r\n]*?coding[:=]\s*([-\w.]+)|[^\r\n]*?\r?\n[^\r\n]*?coding[:=]\s*([-\w.]+)'
)
RE_NON_PRINTABLE_ASCII = re.compile(br"[^ -~]+")


class PythonFilter(filters.Filter):
    """Spelling Python."""

    MODULE = 0
    FUNCTION = 1
    CLASS = 2

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        self.comments = options.get('comments', True) is True
        self.docstrings = options.get('docstrings', True) is True
        self.bytes = options.get('bytes', False) is True
        self.group_comments = options.get('group_comments', False) is True
        super(PythonFilter, self).__init__(options, default_encoding)

    def header_check(self, content):
        """Special Python encoding check."""

        encode = None

        m = RE_PY_ENCODE.match(content)
        if m:
            if m.group(1):
                encode = m.group(1).decode('ascii')
            elif m.group(2):
                encode = m.group(2).decode('ascii')
        if encode is None:
            encode = 'utf-8'
        return encode

    def get_ascii(self, text):
        """Retrieve ASCII text from byte string."""

        return RE_NON_PRINTABLE_ASCII.sub(r' ', text).decode('ascii')

    def _filter(self, text, context, encoding):
        """Retrieve the Python docstrings."""

        docstrings = []
        comments = []
        prev_token_type = tokenize.NEWLINE
        indent = ''
        name = None
        stack = [(context, 0, self.MODULE)]

        src = io.StringIO(text)

        for token in tokenizer(src.readline):
            token_type = token[0]
            value = token[1]
            line = str(token[2][0])
            line_num = token[2][0]

            value = token[1]
            line = str(token[2][0])

            # Track function and class ancestry
            if token_type == tokenize.NAME:
                if value in ('def', 'class'):
                    name = value
                elif name:
                    parent = stack[-1][2]
                    prefix = ''
                    if parent != self.MODULE:
                        prefix = '.' if parent == self.CLASS else ', '
                    if name == 'class':
                        stack.append(('%s%s' % (prefix, value), len(indent), self.CLASS))
                    elif name == 'def':
                        stack.append(('%s%s()' % (prefix, value), len(indent), self.FUNCTION))
                    name = None

            if token_type == tokenize.COMMENT and self.comments:
                # Capture comments
                if (
                    self.group_comments and
                    prev_token_type == tokenize.NL and
                    comments and (comments[-1][2] + 1) == line_num
                ):
                    # Group multiple consecutive comments
                    comments[-1][0] += '\n' + value[1:]
                    comments[-1][2] = line_num
                else:
                    if len(stack) > 1:
                        loc = "%s(%s): %s" % (stack[0][0], line, ''.join([crumb[0] for crumb in stack[1:]]))
                    else:
                        loc = "%s(%s)" % (stack[0][0], line)
                    comments.append([value[1:], loc, line_num])
            if token_type == tokenize.STRING:
                # Capture docstrings.
                # If we captured an `INDENT` or `NEWLINE` previously we probably have a docstring.
                # `NL` seems to be a different thing.
                if prev_token_type in PREV_DOC_TOKENS:
                    if self.docstrings:
                        value = value.strip()
                        string = textwrap.dedent(eval(value))

                        if not isinstance(string, str):
                            # Since docstrings should be readable and printable,
                            # if byte string assume `ascii`.
                            string = string.decode('ascii')
                        loc = "%s(%s): %s" % (stack[0][0], line, ''.join([crumb[0] for crumb in stack[1:]]))
                        docstrings.append(filters.SourceText(string, loc, encoding, 'py-docstring'))

            if token_type == tokenize.INDENT:
                indent = value
            elif token_type == tokenize.DEDENT:
                indent = indent[:-4]
                if len(stack) > 1 and len(indent) <= stack[-1][1]:
                    stack.pop()

            prev_token_type = token_type

        final_comments = []
        for comment in comments:
            final_comments.append(filters.SourceText(textwrap.dedent(comment[0]), comment[1], encoding, 'py-comment'))

        return docstrings + final_comments

    def filter(self, source_file, encoding):  # noqa A001
        """Parse Python file returning content."""

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            return self._filter(f.read(), source_file, encoding)

    def sfilter(self, source):
        """Filter."""

        return self._filter(source.text, source.context, source.encoding)


def get_plugin():
    """Return the filter."""

    return PythonFilter
