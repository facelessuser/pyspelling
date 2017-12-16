"""Markdown parsing."""
from __future__ import unicode_literals
from .. import parsers
import codecs
from ..filters import markdown_filter


class MarkdownParser(parsers.Parser):
    """Spelling Python."""

    FILE_PATTERNS = ('*.md', '*.markdown')

    def __init__(self, config, encoding='ascii'):
        """Initialization."""

        self.filter = markdown_filter.MarkdownFilter(config)
        super(MarkdownParser, self).__init__(config, encoding)

    def parse_file(self, source_file):
        """Parse Markdown file."""

        encoding = self.detect_encoding(source_file)
        try:
            with codecs.open(source_file, 'r', encoding=encoding) as f:
                text = f.read()
            html = [parsers.SourceText(self.filter.filter(text), source_file, encoding, 'markdown')]
        except Exception:
            html = [parsers.SourceText('', source_file, 'bin', 'binary')]
        return html


def get_parser():
    """Return the parser."""

    return MarkdownParser
