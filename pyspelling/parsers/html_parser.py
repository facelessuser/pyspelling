"""
HTML parsing.

Detect encoding from HTML header.
"""
from .. import parsers
import re
import codecs

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

    EXTENSIONS = ('*.html', '*.htm')
    DECODER = HTMLDecoder

    def parse_file(self, source_file):
        """Parse HTML file."""

        encoding = self.detect_encoding(source_file)
        try:
            with codecs.open(source_file, 'r', encoding=encoding) as f:
                text = f.read()
            html = [parsers.SourceText(text, source_file, encoding, 'html')]
        except Exception as e:
            html = [parsers.SourceText('', source_file, 'bin', 'binary')]
        return html


def get_parser():
    """Return the parser."""

    return HTMLParser
