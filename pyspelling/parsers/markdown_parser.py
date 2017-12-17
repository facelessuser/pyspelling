"""Markdown parsing."""
from __future__ import unicode_literals
from .. import parsers
import codecs
from ..filters import markdown_filter
from .. import util


class MarkdownParser(parsers.Parser):
    """Spelling Python."""

    FILE_PATTERNS = ('*.md', '*.markdown')

    def __init__(self, config, default_encoding='ascii'):
        """Initialization."""

        self.filter = markdown_filter.MarkdownFilter(config)
        super(MarkdownParser, self).__init__(config, default_encoding)

    def parse_file(self, source_file, encoding):
        """Parse Markdown file."""

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            text = f.read()
        content = [util.SourceText(self.filter.filter(text, encoding), source_file, encoding, 'markdown')]

        return content


def get_parser():
    """Return the parser."""

    return MarkdownParser
