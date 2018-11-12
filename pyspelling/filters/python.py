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
import unicodedata

tokenizer = tokenize.generate_tokens
PREV_DOC_TOKENS = (tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE, tokenize.ENCODING)

RE_PY_ENCODE = re.compile(
    br'^[^\r\n]*?coding[:=]\s*([-\w.]+)|[^\r\n]*?\r?\n[^\r\n]*?coding[:=]\s*([-\w.]+)'
)
RE_NON_PRINTABLE_ASCII = re.compile(br"[^ -~]+")


BACK_SLASH_TRANSLATION = {
    "\\a": '\a',
    "\\b": '\b',
    "\\f": '\f',
    "\\r": '\r',
    "\\t": '\t',
    "\\n": '\n',
    "\\v": '\v',
    "\\\\": '\\',
    "\n": ''
}

RE_ESC = re.compile(
    r'''(\\[abfrtnv\\\n])|(\\U[\da-fA-F]{8}|\\u[\da-fA-F]{4}|\\x[\da-fA-F]{2})|(\\[0-7]{1,3})|(\N\{[^}{]*\})'''
)

RE_BESC = re.compile(
    r'''(\\[abfrtnv\\\n])|(\\x[\da-fA-F]{2})|(\\[0-7]{1,3})'''
)

RE_FESC = re.compile(
    r'''(?x)
    (\\[abfrtnv\\\n])|
    (\\U[\da-fA-F]{8}|\\u[\da-fA-F]{4}|\\x[\da-fA-F]{2})|
    (\\[0-7]{1,3})|
    (\N\{\{[^}{]*\}\})|
    (\{\{)|
    (\{[^}{]*\})
    '''
)

RE_FBESC = re.compile(
    r'''(\\[abfrtnv\\\n])|(\\x[\da-fA-F]{2})|(\\[0-7]{1,3})(\{\{|\}\})|(\{[^}{]*\})'''
)

RE_STRING_TYPE = re.compile(r'''((?:r|u|f|b)+)?(\'''|"""|'|")(.*?)\2''', re.I | re.S)


class PythonFilter(filters.Filter):
    """Spelling Python."""

    MODULE = 0
    FUNCTION = 1
    CLASS = 2

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super().__init__(options, default_encoding)

    def get_default_config(self):
        """Get default configuration."""

        return {
            'comments': True,
            'docstrings': True,
            'strings': False,
            'group_comments': False
        }

    def replace_escapes(self, m):
        """Replace escapes."""

        esc = m.group(0)
        if m.group(1):
            return BACK_SLASH_TRANSLATION[esc]
        elif m.group(2):
            try:
                esc = chr(int(esc[2:], 16))
            except:
                pass
            return esc
        elif m.group(3):
            value = int(esc[1:], 8)
            return chr(value)
        elif m.group(4):
            try:
                esc = unicodedata.lookup(esc[3:-1])
            except:
                pass
            return esc

    def replace_format_escapes(self, m):
        """Replace format escapes."""

        if m.group(5):
            return m.group(0)
        elif m.group(6):
            return ' '
        return replace_escapes(m)

    def replace_format_byte_escapes(self, m):
        """Replace escapes."""

        if m.group(5):
            return m.group(0)
        elif m.group(6):
            return ' '
        return replace_byte_escapes(m)

    def replace_byte_escapes(self, m):
        """Replace escapes."""

        esc = m.group(0)
        if m.group(1):
            return BACK_SLASH_TRANSLATION[esc]
        elif m.group(2):
            try:
                esc = chr(int(esc[2:], 16))
            except:
                pass
            return esc
        elif m.group(3):
            value = int(esc[1:], 8)
            if value > 255:
                value -= 256
            return chr(value)

    def process_escapes(self, string):
        """Process escapes."""

        m = RE_STRING_TYPE.match(self.norm_nl(string))
        stype = m.group(1).lower() if m.group(1) else ''
        content = m.group(3)
        if 'r' in stype:
            return content
        if 'b' in stype:
            if 'f' in stype:
                RE_FBESC.sub(self.replace_format_byte_escapes, content)
            else:
                return RE_BESC.sub(self.replace_byte_escapes, content)
        if 'f' in stype:
            return RE_FESC.sub(self.replace_format_escapes, content)
        return RE_ESC.sub(self.replace_escapes, content)

    def setup(self):
        """Setup."""

        self.comments = self.config['comments']
        self.docstrings = self.config['docstrings']
        self.strings = self.config['strings']
        self.group_comments = self.config['group_comments']

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
        strings = []
        comments = []
        prev_token_type = tokenize.NEWLINE
        indent = ''
        name = None
        stack = [(context, 0, self.MODULE)]
        last_comment = False

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
                    last_comment and
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
                # `NL` means end of line, but not the end of the Python code line (line continuation).
                if prev_token_type in PREV_DOC_TOKENS:
                    if self.docstrings:
                        value = value.strip()
                        string = textwrap.dedent(self.process_escapes(value))
                        loc = "%s(%s): %s" % (stack[0][0], line, ''.join([crumb[0] for crumb in stack[1:]]))
                        docstrings.append(filters.SourceText(string, loc, encoding, 'py-docstring'))
                elif self.strings:
                    value = value.strip()
                    string = textwrap.dedent(self.process_escapes(value))
                    loc = "%s(%s): %s" % (stack[0][0], line, ''.join([crumb[0] for crumb in stack[1:]]))
                    strings.append(filters.SourceText(string, loc, encoding, 'py-string'))

            if token_type == tokenize.INDENT:
                indent = value
            elif token_type == tokenize.DEDENT:
                indent = indent[:-4]
                if len(stack) > 1 and len(indent) <= stack[-1][1]:
                    stack.pop()

            # We purposefully avoid storing comments as comments can come before docstrings,
            # and that can mess up our logic. So if the token is a comment we won't track it,
            # and comments are always followed with `NL` so we ignore that as well.
            # We only care that docstrings are preceded by `NEWLINE`.
            if token_type != tokenize.COMMENT and not (last_comment and token_type == tokenize.NL):
                prev_token_type = token_type
                last_comment = False
            else:
                last_comment = True

        final_comments = []
        for comment in comments:
            final_comments.append(filters.SourceText(textwrap.dedent(comment[0]), comment[1], encoding, 'py-comment'))

        return docstrings + final_comments + strings

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
