"""
Python parsing.

Parse Python docstrings.
"""
from .. import parsers
import re
import tokenize
import textwrap
import codecs
from .. import util
# import markdown

if util.PY3:
    tokenizer = tokenize.tokenize
    PREV_DOC_TOKENS = (tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE, tokenize.ENCODING)
else:
    tokenizer = tokenize.generate_tokens
    PREV_DOC_TOKENS = (tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE)


class PythonDecoder(parsers.Decoder):
    """Detect Python encoding."""

    RE_PY_ENCODE = re.compile(
        br'^[^\r\n]*?coding[:=]\s*([-\w.]+)|[^\r\n]*?\r?\n[^\r\n]*?coding[:=]\s*([-\w.]+)'
    )

    def special_encode_check(self, content, ext):
        """Special Python encoding check."""

        encode = None

        m = self.RE_PY_ENCODE.match(content)
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

        # self.markdown = config.get('markdown', False)
        # self.extensions = []
        # self.extension_configs = {}
        # for item in config.get('markdown_extensions', []):
        #     if isinstance(item, util.ustr):
        #         self.extensions.append(item)
        #     else:
        #         k, v = list(item.items())[0]
        #         self.extensions.append(k)
        #         if v is not None:
        #             self.extension_configs[k] = v
        self.comments = config.get('comments', True) is True
        self.docstrings = config.get('docstrings', True) is True
        self.strings = config.get('strings', True) is True
        super(PythonParser, self).__init__(config, encoding)

    def detect_encoding(self, source_file):
        """Get default encoding."""

        if util.PY3:
            # In Py3, the tokenizer will tell us what the encoding is.
            encoding = 'ascii'
        else:
            encoding = self.DECODER().guess(source_file, verify=False)
        return encoding

    def parse_docstrings(self, source_file):
        """Retrieve the Python docstrings."""

        docstrings = []
        comments = []
        strings = []
        prev_token_type = tokenize.NEWLINE
        indent = ''
        name = None
        stack = [(source_file, 0, self.MODULE)]

        encoding = self.detect_encoding(source_file)

        # if self.markdown:
        #     md = markdown.Markdown(extensions=self.extensions, extension_configs=self.extension_configs)
        # else:
        #     md = None

        with open(source_file, 'rb') as source:
            for token in tokenizer(source.readline):
                token_type = token[0]
                value = token[1]
                line = util.ustr(token[2][0])

                if util.PY3 and token_type == tokenize.ENCODING:
                    encoding = value

                value = token[1] if util.PY3 else token[1].decode(encoding)
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
                        loc ="%s(%s): %s" % (stack[0][0], line, ''.join([crumb[0] for crumb in stack[1:]]))
                    else:
                        loc = "%s(%s)" % (stack[0][0], line)
                    comments.append(parsers.SourceText(value, loc, encoding, 'comment'))
                if token_type == tokenize.STRING:
                    # Capture docstrings
                    # If previously we captured an INDENT or NEWLINE previously we probably have a docstring.
                    # NL seems to be a different thing.
                    if prev_token_type in PREV_DOC_TOKENS:
                        if self.docstrings:
                            string = textwrap.dedent(eval(value.strip()))
                            if not isinstance(string, util.ustr):
                                string = string.decode(encoding)
                            # if md:
                            #     string = md.convert(string)
                            #     md.reset()
                            loc = "%s(%s): %s" % (stack[0][0], line, ''.join([crumb[0] for crumb in stack[1:]]))
                            docstrings.append(parsers.SourceText(string, loc, encoding, 'docstring'))
                    elif self.strings:
                        string = eval(value.strip())
                        if not isinstance(string, util.ustr):
                            string = string.decode(encoding)
                        loc = "%s(%s): %s" % (stack[0][0], line, ''.join([crumb[0] for crumb in stack[1:]]))
                        strings.append(parsers.SourceText(string, loc, encoding, 'string'))

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
    """Return the parser"""

    return PythonParser
