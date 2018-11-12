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
    r'''(?x)
    (?P<special>\\[abfrtnv\\\n])|
    (?P<char>\\U[\da-fA-F]{8}|\\u[\da-fA-F]{4}|\\x[\da-fA-F]{2})|
    (?P<oct>\\[0-7]{1,3})|
    (?P<name>\\N\{[^}{]*\})
    '''
)

RE_BESC = re.compile(
    r'''(?x)
    (?P<special>\\[abfrtnv\\\n])|
    (?P<char>\\x[\da-fA-F]{2})|
    (?P<oct>\\[0-7]{1,3})
    '''
)

RE_FESC = re.compile(
    r'''(?x)
    (?P<special>\\[abfrtnv\\\n])|
    (?P<char>\\U[\da-fA-F]{8}|\\u[\da-fA-F]{4}|\\x[\da-fA-F]{2})|
    (?P<oct>\\[0-7]{1,3})|
    (?P<name>\\N\{\{[^}{]*\}\})|
    (?P<fesc>\{\{)|
    (?P<format>\{[^}{]*\})
    '''
)

FE_RFESC = re.compile(
    r'''(?x)
    (?P<fesc>\{\{)|
    (?P<format>\{[^}{]*\})
    '''
)

RE_STRING_TYPE = re.compile(r'''((?:r|u|f|b)+)?(\'''|"""|'|")(.*?)\2''', re.I | re.S)

RE_NON_PRINTABLE = re.compile(r'[\x00-\x0f\x0b-\x1f\x7f-\xff]+')


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
            'group_comments': False,
            'allowed': 'u,f'
        }

    def setup(self):
        """Setup."""

        self.comments = self.config['comments']
        self.docstrings = self.config['docstrings']
        self.strings = self.config['strings']
        self.group_comments = self.config['group_comments']
        self.allowed = set()
        for item in self.config['allowed'].split(','):
            self.allowed.add(self.eval_string_type(item))

    def validate_options(self, k, v):
        """Validate options."""

        if k == 'allowed':
            for item in v.split(','):
                for c in item:
                    if c.lower() not in 'rbuf':
                        raise ValueError("{}: '{}' is not a valid string type".format(self.__class__.__name__, c))

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

    def eval_string_type(self, stype):
        """Evaluate string type."""

        return tuple(sorted(set([c.lower() for c in stype if c.lower() != 'u'])))

    def replace_unicode(self, m):
        """Replace escapes."""

        groups = m.groupdict()
        esc = m.group(0)
        if groups.get('fesc'):
            return m.group(0)
        elif groups.get('format'):
            return ' '
        elif groups.get('special'):
            return BACK_SLASH_TRANSLATION[esc]
        elif groups.get('char'):
            try:
                esc = chr(int(esc[2:], 16))
            except Exception:
                pass
            return esc
        elif groups.get('oct'):
            value = int(esc[1:], 8)
            return chr(value)
        elif groups.get('named'):
            try:
                esc = unicodedata.lookup(esc[3:-1])
            except Exception:
                pass
            return esc

    def replace_bytes(self, m):
        """Replace escapes."""

        esc = m.group(0)
        if m.group('special'):
            return BACK_SLASH_TRANSLATION[esc]
        elif m.group('char'):
            try:
                esc = chr(int(esc[2:], 16))
            except Exception:
                pass
            return esc
        elif m.group('oct'):
            value = int(esc[1:], 8)
            if value > 255:
                value -= 256
            return chr(value)

    def process_strings(self, string):
        """Process escapes."""

        m = RE_STRING_TYPE.match(string)
        stype = self.eval_string_type(m.group(1) if m.group(1) else '')
        if stype not in self.allowed:
            return '', False
        is_bytes = 'b' in stype
        is_raw = 'r' in stype
        is_format = 'f' in stype
        content = m.group(3)
        if is_raw and is_format:
            string = self.norm_nl(FE_RFESC.sub(self.replace_unicode, content))
        elif is_raw:
            string = self.norm_nl(content)
        elif is_bytes:
            string = self.norm_nl(RE_BESC.sub(self.replace_bytes, content))
        elif is_format:
            string = self.norm_nl(RE_FESC.sub(self.replace_unicode, content))
        else:
            string = self.norm_nl(RE_ESC.sub(self.replace_unicode, content))

        return textwrap.dedent(RE_NON_PRINTABLE.sub(' ', string) if is_bytes else string), is_bytes

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
                        string, is_bytes = self.process_strings(value)
                        if string:
                            loc = "%s(%s): %s" % (stack[0][0], line, ''.join([crumb[0] for crumb in stack[1:]]))
                            docstrings.append(
                                filters.SourceText(string, loc, 'ascii' if is_bytes else encoding, 'py-docstring')
                            )
                elif self.strings:
                    value = value.strip()
                    string, is_bytes = self.process_strings(value)
                    if string:
                        loc = "%s(%s): %s" % (stack[0][0], line, ''.join([crumb[0] for crumb in stack[1:]]))
                        strings.append(filters.SourceText(string, loc, 'ascii' if is_bytes else encoding, 'py-string'))

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
