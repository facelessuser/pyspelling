"""
HTML parsing.

Detect encoding from HTML header.
"""
from __future__ import unicode_literals
from .. import parsers
import re
import codecs
from ..filters import html_filter

RE_HTML_ENCODE = re.compile(
    br'''(?x)
    <meta(?!\s*(?:name|value)\s*=)(?:[^>]*?content\s*=[\s"']*)?(?:[^>]*?)[\s"';]*charset\s*=[\s"']*([^\s"'/>]*)
    '''
)


class HTMLDecoder(parsers.Decoder):
    """Detect HTML encoding."""

    def special_encode_check(self, content, ext):
        """Special HTML encoding check."""

        encode = None
        m = RE_HTML_ENCODE.search(content)
        if m:
            enc = m.group(1).decode('ascii')
            try:
                codecs.getencoder(enc)
                encode = enc
            except LookupError:
                pass
        else:
            print('No match')
        return encode


class HTMLParser(parsers.Parser):
    """Spelling Python."""

    FILE_PATTERNS = ('*.html', '*.htm')
    DECODER = HTMLDecoder

    def __init__(self, config, encoding='ascii'):
        """Initialization."""

        self.filter = html_filter.HTMLFilter(config)
        super(HTMLParser, self).__init__(config, encoding)

    def parse_file(self, source_file):
        """Parse HTML file."""

        encoding = self.detect_encoding(source_file)
        try:
            with codecs.open(source_file, 'r', encoding=encoding) as f:
                text = f.read()
            html = [parsers.SourceText(self.filter.filter(text), source_file, encoding, 'html')]
        except Exception:
            html = [parsers.SourceText('', source_file, 'bin', 'binary')]
        return html


def get_parser():
    """Return the parser."""

    return HTMLParser
