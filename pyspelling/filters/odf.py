"""
Open Document Format (ODF) filter.

Parse the `text` namespace in `content.xml` in ODF zip files.
"""
from __future__ import unicode_literals
import zipfile
import io
import html
from . import xml


class OdfFilter(xml.XmlFilter):
    """Spelling Python."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super(OdfFilter, self).__init__(options, default_encoding)

        self.comments = False
        self.attributes = []
        self.parser = 'xml'
        self.type = 'odf'
        self.ignores = []
        self.captures = self.process_selectors(*['text|*'])
        self.namespaces = {'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}

    def _detect_encoding(self, source_file):
        """Detect encoding."""

        return ''

    def get_content(self, odf):
        """Get content."""

        with zipfile.ZipFile(odf, 'r') as z:
            content = z.read('content.xml')

        with io.BytesIO(content) as b:
            encoding = self._analyze_file(b)
            if encoding is None:
                encoding = self.default_encoding
            b.seek(0)
            content = b.read().decode(encoding)

        self.odf_encoding = encoding

        return content

    def is_paragraph(self, el):
        """Check if paragraph."""

        return el.name == 'p' and el.namespace and el.namespace == self.namespaces["text"]

    def store_blocks(self, el, blocks, text, is_root):
        """Store the text as desired."""

        if is_root or self.is_paragraph(el):
            content = html.unescape(''.join(text))
            if content:
                blocks.append((content, self.construct_selector(el)))
            text = []
        return text

    def filter(self, source_file, encoding):  # noqa A001
        """Parse XML file."""

        return self._filter(self.get_content(source_file), source_file, self.odf_encoding)

    def sfilter(self, source):
        """Filter."""

        return self._filter(
            self.get_content(io.BytesIO(source.text.encode(source.encoding))),
            source.context,
            self.odf_encoding
        )


def get_plugin():
    """Return the filter."""

    return OdfFilter
