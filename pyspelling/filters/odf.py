"""
Open Document Format (ODF) filter.

Parse the `text` namespace in `content.xml` in ODF zip files.
"""
from __future__ import unicode_literals
import zipfile
import io
import html
import bs4
import codecs
from .. import filters
from . import xml
from wcmatch import glob
from ..util.css_selectors import SelectorMatcher

MIMEMAP = {
    'application/vnd.oasis.opendocument.spreadsheet': 'ods',
    'application/vnd.oasis.opendocument.presentation': 'odp',
    'application/vnd.oasis.opendocument.text': 'odt'
}


class OdfFilter(xml.XmlFilter):
    """Spelling Python."""

    FLAGS = glob.G | glob.N | glob.B

    default_capture = ['text|*']

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super().__init__(options, default_encoding)

    def get_default_config(self):
        """Get default configuration."""

        return {}

    def setup(self):
        """Setup."""

        self.additional_context = ''
        self.comments = False
        self.attributes = []
        self.parser = 'xml'
        self.type = None
        self.filepattern = 'content.xml'
        self.namespaces = {
            'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
            'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'
        }
        self.ignores = SelectorMatcher(
            '', 'xml', []
        )
        self.captures = SelectorMatcher(
            ','.join(self.default_capture), 'xml', self.namespaces
        )

    def has_bom(self, filestream):
        """Check if has BOM."""

        content = filestream.read(4)
        if content == b'PK\x03\x04':
            # Zip file found.
            # Return `BINARY_ENCODE` as content is binary type,
            # but don't return None which means we don't know what we have.
            return filters.BINARY_ENCODE
        # Not a zip file, so maybe a flat ODF XML file.
        return super().has_bom(filestream)

    def determine_file_type(self, z):
        """Determine file type."""

        mimetype = z.read('mimetype').decode('utf-8').strip()
        self.type = MIMEMAP[mimetype]

    def get_zip_content(self, filename):
        """Get zip content."""

        with zipfile.ZipFile(filename, 'r') as z:
            self.determine_file_type(z)
            for item in z.infolist():
                if glob.globmatch(item.filename, glob.globsplit(self.filepattern, flags=self.FLAGS), flags=self.FLAGS):
                    yield z.read(item.filename), item.filename

    def get_content(self, zipbundle):
        """Get content."""

        for content, filename in self.get_zip_content(zipbundle):
            with io.BytesIO(content) as b:
                encoding = self._analyze_file(b)
                if encoding is None:
                    encoding = self.default_encoding
                b.seek(0)
                text = b.read().decode(encoding)
            yield text, filename, encoding

    def content_break(self, el):
        """Break on specified boundaries."""

        should_break = False
        if self.type == 'odp':
            if el.name == 'page' and el.namespace and el.namespace == self.namespaces['draw']:
                should_break = True
        return should_break

    def soft_break(self, el, text):
        """Apply soft break if needed."""

        if el.name == 'p' and el.namespace and el.namespace == self.namespaces["text"]:
            text.append('\n')

    def store_blocks(self, el, blocks, text, force_root):
        """Store the text as desired."""

        self.soft_break(el, text)

        if force_root or el.parent is None or self.content_break(el):
            content = html.unescape(''.join(text))
            if content:
                blocks.append((content, self.additional_context + self.construct_selector(el)))
            text = []
        return text

    def extract_tag_metadata(self, el):
        """Extract meta data."""

        if self.type == 'odp':
            if el.namespace and el.namespace == self.namespaces['draw'] and el.name == 'page-thumbnail':
                name = el.attrs.get('draw:page-number', '')
                self.additional_context = 'slide{}:'.format(name)
        super().extract_tag_metadata(el)

    def reset(self):
        """Reset anything needed on each iteration."""

        self.type = None
        self.additional_context = ""
        super().reset()

    def get_sub_node(self, node):
        """Extract node from document if desired."""

        subnode = node.find('office:document')
        if subnode:
            mimetype = subnode.attrs['office:mimetype']
            self.type = MIMEMAP[mimetype]
            node = node.find('office:body')
        return node

    def _filter(self, text, context, encoding):
        """Filter the source text."""

        content = []
        soup = bs4.BeautifulSoup(text, self.parser)
        soup = self.get_sub_node(soup)
        blocks, attributes, comments = self.to_text(soup, force_root=not isinstance(soup, bs4.BeautifulSoup))
        if self.comments:
            for c, desc in comments:
                content.append(filters.SourceText(c, context + ': ' + desc, encoding, self.type + 'comment'))
        if self.attributes:
            for a, desc in attributes:
                content.append(filters.SourceText(a, context + ': ' + desc, encoding, self.type + 'attribute'))
        for b, desc in blocks:
            content.append(filters.SourceText(b, context + ': ' + desc, encoding, self.type + 'content'))
        return content

    def filter(self, source_file, encoding):  # noqa A001
        """Parse XML file."""

        sources = []
        if encoding:
            with codecs.open(source_file, 'r', encoding=encoding) as f:
                src = f.read()
            sources.extend(self._filter(src, source_file, encoding))
        else:
            for content, filename, enc in self.get_content(source_file):
                sources.extend(self._filter(content, source_file, enc))
        return sources

    def sfilter(self, source):
        """Filter."""

        sources = []
        if source.text[:4].encode(source.encoding) != b'PK\x03\x04':
            sources.extend(self._filter(source.text, source.context, source.encoding))
        else:
            for content, filename, enc in self.get_content(io.BytesIO(source.text.encode(source.encoding))):
                sources.extend(self._filter(content, source.context, enc))
        return sources


def get_plugin():
    """Return the filter."""

    return OdfFilter
