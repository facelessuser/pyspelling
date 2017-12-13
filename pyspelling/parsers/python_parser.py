"""
Python parsing.

Parse Python docstrings.
"""
from __future__ import unicode_literals
from .. import parsers
import re
import textwrap
import codecs
import tokenize
import ast
from .. import util

if util.PY3:
    tokenizer = tokenize.tokenize
    PREV_DOC_TOKENS = (tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE, tokenize.ENCODING)
else:
    tokenizer = tokenize.generate_tokens
    PREV_DOC_TOKENS = (tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE)

RE_PY_ENCODE = re.compile(
    br'^[^\r\n]*?coding[:=]\s*([-\w.]+)|[^\r\n]*?\r?\n[^\r\n]*?coding[:=]\s*([-\w.]+)'
)
RE_NON_PRINTABLE_ASCII = re.compile(br"[^ -~]+")


class PythonDecoder(parsers.Decoder):
    """Detect Python encoding."""

    def special_encode_check(self, content, ext):
        """Special Python encoding check."""

        encode = None

        m = RE_PY_ENCODE.match(content)
        if m:
            if m.group(1):
                enc = m.group(1).decode('ascii')
            elif m.group(2):
                enc = m.group(2).decode('ascii')
            try:
                codecs.getencoder(enc)
                encode = enc
            except LookupError:
                pass
        if encode is None:
            encode = 'ascii'
        return encode


class PythonParser(parsers.Parser):
    """Spelling Python."""

    EXTENSIONS = ('*.py', '*.pyw')
    DECODER = PythonDecoder

    MODULE = 0
    FUNCTION = 1
    CLASS = 2

    def __init__(self, config, encoding='ascii'):
        """Initialization."""

        self.comments = config.get('comments', True) is True
        self.docstrings = config.get('docstrings', True) is True
        self.strings = config.get('strings', True) is True
        self.bytes = config.get('bytes', False) is True
        super(PythonParser, self).__init__(config, encoding)

    def is_py2_unicode_literals(self, text, source_file):
        """Check if Python 2 Unicode literals is used."""

        uliterals = False
        root = ast.parse(text, source_file)

        for node in ast.iter_child_nodes(root):
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module.split('.')
            else:
                continue

            if module[0] != '__future__':
                continue

            for n in node.names:
                if n.name and n.name.split('.')[0] == 'unicode_literals':
                    uliterals = True
                    break
        return uliterals

    def detect_encoding(self, source_file):
        """Get default encoding."""

        if util.PY3:
            # In Py3, the tokenizer will tell us what the encoding is.
            encoding = 'ascii'
        else:
            encoding = self.DECODER().guess(source_file, verify=False)
        return encoding

    def get_ascii(self, text):
        """Retrieve ASCII text from byte string."""

        return RE_NON_PRINTABLE_ASCII.sub(r' ', text).decode('ascii')

    def parse_docstrings(self, source_file):
        """Retrieve the Python docstrings."""

        docstrings = []
        comments = []
        strings = []
        prev_token_type = tokenize.NEWLINE
        indent = ''
        name = None
        stack = [(source_file, 0, self.MODULE)]
        uliterals = True

        encoding = self.detect_encoding(source_file)

        with open(source_file, 'rb') as source:

            if not util.PY3:
                uliterals = self.is_py2_unicode_literals(source.read(), source_file)
                source.seek(0)

            for token in tokenizer(source.readline):
                token_type = token[0]
                value = token[1]
                line = util.ustr(token[2][0])

                if util.PY3 and token_type == tokenize.ENCODING:
                    encoding = value

                value = token[1]
                line = util.ustr(token[2][0])

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
                    if len(stack) > 1:
                        loc = "%s(%s): %s" % (stack[0][0], line, ''.join([crumb[0] for crumb in stack[1:]]))
                    else:
                        loc = "%s(%s)" % (stack[0][0], line)
                    comments.append(parsers.SourceText(value, loc, encoding, 'comment'))
                if token_type == tokenize.STRING:
                    # Capture docstrings
                    # If previously we captured an INDENT or NEWLINE previously we probably have a docstring.
                    # NL seems to be a different thing.
                    if prev_token_type in PREV_DOC_TOKENS:
                        if self.docstrings:
                            value = value.strip()
                            if not util.PY3 and not value.startswith((b'u', b'b')):
                                value = (b'u' if uliterals else b'b') + value
                            string = textwrap.dedent(eval(value))

                            if not isinstance(string, util.ustr):
                                # Since docstrings should be readable and printable,
                                # if byte string assume 'ascii'.
                                string = string.decode('ascii')
                            loc = "%s(%s): %s" % (stack[0][0], line, ''.join([crumb[0] for crumb in stack[1:]]))
                            docstrings.append(parsers.SourceText(string, loc, encoding, 'docstring'))
                    elif self.strings:
                        value = value.strip()
                        if not util.PY3 and not value.startswith((b'u', b'b')):
                            value = (b'u' if uliterals else b'b') + value
                        string = textwrap.dedent(eval(value))
                        if isinstance(string, util.ustr) or self.bytes:
                            string_type = 'string'
                            if not isinstance(string, util.ustr):
                                string = self.get_ascii(string)
                                string_type = 'bytes'
                            loc = "%s(%s): %s" % (stack[0][0], line, ''.join([crumb[0] for crumb in stack[1:]]))
                            strings.append(parsers.SourceText(string, loc, encoding, string_type))

                if token_type == tokenize.INDENT:
                    indent = value
                elif token_type == tokenize.DEDENT:
                    indent = indent[:-4]
                    if len(stack) > 1 and len(indent) <= stack[-1][1]:
                        stack.pop()

                prev_token_type = token_type

        return docstrings + comments + strings

    def parse_file(self, source_file):
        """Parse Python file returning docstrings."""

        try:
            docstrings = self.parse_docstrings(source_file)
        except Exception as e:
            print(e)
            docstrings = [parsers.SourceText('', source_file, 'bin', 'binary')]
        return docstrings


def get_parser():
    """Return the parser."""

    return PythonParser
