"""
Open Document Format (ODF) filter.

Parse the `text` namespace in `content.xml` in ODF zip files.
"""
from __future__ import unicode_literals
import zipfile
import io
import html
from . import xml
from wcmatch import glob

MIMEMAP = {
    'application/vnd.oasis.opendocument.spreadsheet': 'ods',
    'application/vnd.oasis.opendocument.presentation': 'odp',
    'application/vnd.oasis.opendocument.text': 'odt'
}


class OdfFilter(xml.XmlFilter):
    """Spelling Python."""

    FLAGS = glob.G | glob.N | glob.B

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super(OdfFilter, self).__init__(options, default_encoding)

        self.additional_context = ''
        self.comments = False
        self.attributes = []
        self.parser = 'xml'
        self.type = 'odf'
        self.filepattern = 'content.xml'
        self.ignores = []
        self.captures = self.process_selectors(*['text|*'])
        self.slide_num = None
        self.namespaces = {
            'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
            'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'
        }

    def _detect_encoding(self, source_file):
        """Detect encoding."""

        return ''

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

    def store_blocks(self, el, blocks, text, is_root):
        """Store the text as desired."""

        self.soft_break(el, text)

        if is_root or self.content_break(el):
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

    def reset(self):
        """Reset anything needed on each iteration."""

        self.additional_context = ""

    def filter(self, source_file, encoding):  # noqa A001
        """Parse XML file."""

        sources = []
        for content, filename, enc in self.get_content(source_file):
            sources.extend(self._filter(content, source_file, enc))
        return sources

    def sfilter(self, source):
        """Filter."""

        sources = []
        for content, filename, enc in self.get_content(io.BytesIO(source.text.encode(source.encoding))):
            self.extend(self._filter(content, source.context, enc))
        return sources


def get_plugin():
    """Return the filter."""

    return OdfFilter
