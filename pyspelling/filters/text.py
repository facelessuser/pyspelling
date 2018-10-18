"""Text filter."""
from __future__ import unicode_literals
from .. import filters
import codecs
import unicodedata


class TextFilter(filters.Filter):
    """Spelling Text."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        self.normalize = options.get('normalize', '').upper()
        self.convert_encoding = options.get('convert_encoding', '').lower()
        self.errors = options.get('errors', 'strict').lower()
        if self.convert_encoding:
            self.convert_encoding = codecs.lookup(
                filters.PYTHON_ENCODING_NAMES.get(default_encoding, default_encoding).lower()
            ).name

            # Don't generate content with BOMs
            if (
                self.convert_encoding.startswith(('utf-32', 'utf-16')) and
                not self.convert_encoding.endswith(('le', 'be'))
            ):
                self.convert_encoding += '-le'

            if self.convert_encoding == 'utf-8-sig':
                self.convert_encoding = 'utf-8'

        super(TextFilter, self).__init__(options, default_encoding)

    def convert(self, text, encoding):
        """Convert the text."""

        if self.normalize in ('NFC', 'NFKC', 'NFD', 'NFKD'):
            text = unicodedata.normalize(self.normalize, text)
        if self.convert_encoding:
            text = text.encode(self.convert_encoding, self.errors).decode(self.convert_encoding)
            encoding = self.convert_encoding
        return text, encoding

    def filter(self, source_file, encoding):  # noqa A001
        """Open and filter the file from disk."""

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            text = f.read()

        text, encoding = self.convert(text, encoding)

        return [filters.SourceText(text, source_file, encoding, 'text')]

    def sfilter(self, source):
        """Execute filter."""

        text, encoding = self.convert(source.text, source.encoding)

        return [filters.SourceText(text, source.context, encoding, 'text')]


def get_plugin():
    """Return the filter."""

    return TextFilter
