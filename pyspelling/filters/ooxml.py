"""
Office Open XML file format.

Extract text from `docx`, `pptx`, and `xlsx` files.

Specification: http://officeopenxml.com
"""
from __future__ import unicode_literals
import io
import bs4
from . import odf
import re

DOC_PARAMS = {
    'docx': {
        'filepattern': 'word/{document,header*,footer*,footnotes,endnotes}.xml',
        'namespaces': {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'},
        'captures': ['w|t']
    },
    'pptx': {
        'filepattern': 'ppt/slides/slide*.xml',
        'namespaces': {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'},
        'captures': ['a|t']
    },
    'xlsx': {
        'filepattern': 'xl/sharedStrings.xml',
        'namespaces': {'': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'},
        'captures': ['t']
    }
}

RE_SLIDE = re.compile(r'ppt/(?:slides|slideMasters)/(slide(?:Master)?\d+)\.xml', re.I)
RE_DOCS = re.compile(r'word/(document|header\d+|footer\d+|footnotes|endnotes)\.xml')

MIMEMAP = {
    'word': 'docx',
    'xl': 'xlsx',
    'ppt': 'pptx'
}


class OoxmlFilter(odf.OdfFilter):
    """Spelling Python."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super(OoxmlFilter, self).__init__(options, default_encoding)

        self.comments = False
        self.attributes = []
        self.parser = 'xml'
        self.ignores = []
        self.type = ''
        self.filepattern = ''
        self.captures = []
        self.namespaces = {}

    def _detect_encoding(self, source_file):
        """Detect encoding."""

        return ''

    def determine_file_type(self, z):
        """Determine file type."""

        content = z.read('[Content_Types].xml')
        with io.BytesIO(content) as b:
            encoding = self._analyze_file(b)
            if encoding is None:
                encoding = 'utf-8'
            b.seek(0)
            text = b.read().decode(encoding)
            soup = bs4.BeautifulSoup(text, 'xml')
            for o in soup.find_all('Override'):
                name = o.attrs.get('PartName')
                for k, v in MIMEMAP.items():
                    if name.startswith('/{}/'.format(k)):
                        self.type = v
                        break
                if self.type:
                    break
        self.filepattern = DOC_PARAMS[self.type]['filepattern']
        self.captures = self.process_selectors(*DOC_PARAMS[self.type]['captures'])
        self.namespaces = DOC_PARAMS[self.type]['namespaces']

    def soft_break(self, el, text):
        """Apply soft break."""

        # Break word documents by paragraphs.
        if self.type == 'docx' and el.namespace == self.namespaces['w'] and el.name == 'p':
            text.append('\n')
        # Break slides by paragraphs.
        if self.type == 'pptx' and el.namespace == self.namespaces['a'] and el.name == 'p':
            text.append('\n')

    def content_break(self, el):
        """Break on specified boundaries."""

        should_break = False
        return should_break

    def extract_tag_metadata(self, el):
        """Extract meta data."""

    def get_context(self, filename):
        """Get context."""

        if self.type == 'pptx':
            context = '{}: '.format(RE_SLIDE.search(filename).group(1))
        elif self.type == 'docx':
            context = '{}: '.format(RE_DOCS.match(filename).group(1))
        else:
            context = ''
        return context

    def get_sub_node(self, node):
        """Extract node from document if desired."""

        return node

    def filter(self, source_file, encoding):  # noqa A001
        """Parse XML file."""

        sources = []
        for content, filename, enc in self.get_content(source_file):
            self.additional_context = self.get_context(filename)
            sources.extend(self._filter(content, source_file, enc))
        return sources

    def sfilter(self, source):
        """Filter."""

        sources = []
        for content, filename, enc in self.get_content(io.BytesIO(source.text.encode(source.encoding))):
            self.additional_context = self.get_context(filename)
            self.extend(self._filter(content, source.context, enc))
        return sources


def get_plugin():
    """Return the filter."""

    return OoxmlFilter
