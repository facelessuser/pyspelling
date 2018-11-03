"""
Office Open XML file format.

Extract text from `docx`, `pptx`, and `xlsx` files.

Specification: http://officeopenxml.com
"""
from __future__ import unicode_literals
import io
from . import odf
import re

DOC_TYPES = {
    'document': 'docx',
    'presentation': 'pptx',
    'spreadsheet': 'xlsx'
}

DOC_PARAMS = {
    'docx': {
        'filepattern': 'word/document.xml',
        'namespaces': {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'},
        'captures': ['w|*']
    },
    'pptx': {
        'filepattern': 'ppt/slides/slide*.xml',
        'namespaces': {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'},
        'captures': ['a|*']
    },
    'xlsx': {
        'filepattern': 'xl/sharedStrings.xml',
        'namespaces': {'': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'},
        'captures': ['t']
    }
}

RE_SLIDE = re.compile(r'\bslide(\d+).xml', re.I)


class OoxmlFilter(odf.OdfFilter):
    """Spelling Python."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super(OoxmlFilter, self).__init__(options, default_encoding)

        mode = options.get('mode', 'document')
        if mode not in DOC_TYPES:
            mode = 'document'
        self.comments = False
        self.attributes = []
        self.parser = 'xml'
        self.type = DOC_TYPES[mode]
        self.ignores = []
        self.filepattern = DOC_PARAMS[self.type]['filepattern']
        self.captures = self.process_selectors(*DOC_PARAMS[self.type]['captures'])
        self.namespaces = DOC_PARAMS[self.type]['namespaces']

    def content_break(self, el):
        """Break on specified boundaries."""

        should_break = False
        # Break word documents by paragraphs.
        if self.type == 'docx' and el.namespace == self.namespaces['w'] and el.name == 'p':
            should_break = True
        # Break slides by paragraphs.
        if self.type == 'pptx' and el.namespace == self.namespaces['a'] and el.name == 'p':
            should_break = True
        return should_break

    def filter(self, source_file, encoding):  # noqa A001
        """Parse XML file."""

        sources = []
        for content, filename, enc in self.get_content(source_file):
            if self.type == 'pptx':
                context = ': Slide {}'.format(RE_SLIDE.search(filename).group(1))
            else:
                context = ''
            sources.extend(self._filter(content, source_file + context, enc))
        return sources

    def sfilter(self, source):
        """Filter."""

        sources = []
        for content, filename, enc in self.get_content(io.BytesIO(source.text.encode(source.encoding))):
            if self.type == 'pptx':
                context = ': Slide {}'.format(RE_SLIDE.search(filename).group(1))
            else:
                context = ''
            self.extend(self._filter(content, source.context + context, enc))
        return sources


def get_plugin():
    """Return the filter."""

    return OoxmlFilter
