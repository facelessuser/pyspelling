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

    def header_check(self, content):
        """Special HTML encoding check."""

        encode = None
        m = RE_HTML_ENCODE.search(content)
        if m:
            encode = m.group(1).decode('ascii')
        return encode


class HTMLParser(parsers.Parser):
    """Spelling Python."""

    FILE_PATTERNS = ('*.html', '*.htm')
    DECODER = HTMLDecoder

    def __init__(self, config, default_encoding='ascii'):
        """Initialization."""

        self.filter = html_filter.HTMLFilter(config)
        super(HTMLParser, self).__init__(config, default_encoding)

    def parse_file(self, source_file, encoding):
        """Parse HTML file."""

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            text = f.read()
        content = [parsers.SourceText(self.filter.filter(text, encoding), source_file, encoding, 'html')]

        return content


def get_parser():
    """Return the parser."""

    return HTMLParser
