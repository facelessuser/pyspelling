"""Text filter."""
from __future__ import unicode_literals
from .. import filters
import codecs
import unicodedata


class TextFilter(filters.Filter):
    """Spelling Text."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super().__init__(options, default_encoding)

    def get_default_config(self):
        """Get default configuration."""

        return {
            'normalize': '',
            'convert_encoding': '',
            'errors': 'strict'
        }

    def validate_options(self, k, v):
        """Validate options."""

        super().validate_options(k, v)
        if k == 'errors' and v.lower() not in ('strict', 'replace', 'ignore', 'backslashreplace'):
            raise ValueError("{}: '{}' is not a valid value for '{}'".format(self.__class__.__name, v, k))
        if k == 'normalize' and v.upper() not in ('NFC', 'NFKC', 'NFD', 'NFKD'):
            raise ValueError("{}: '{}' is not a valid value for '{}'".format(self.__class__.__name, v, k))

    def setup(self):
        """Setup."""

        self.normalize = self.config['normalize'].upper()
        self.convert_encoding = self.config['convert_encoding'].lower()
        self.errors = self.config['errors'].lower()

        if self.convert_encoding:
            self.convert_encoding = codecs.lookup(
                filters.PYTHON_ENCODING_NAMES.get(self.default_encoding, self.default_encoding).lower()
            ).name

            # Don't generate content with BOMs
            if (
                self.convert_encoding.startswith(('utf-32', 'utf-16')) and
                not self.convert_encoding.endswith(('le', 'be'))
            ):
                self.convert_encoding += '-le'

            if self.convert_encoding == 'utf-8-sig':
                self.convert_encoding = 'utf-8'

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
