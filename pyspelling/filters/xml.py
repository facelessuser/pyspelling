"""
XML filter.

Detect encoding from XML header.
"""
from __future__ import unicode_literals
from .. import filters
import re
import codecs
import bs4
import html
from ..util.css_selectors import SelectorMatcher

NON_CONTENT = (bs4.Doctype, bs4.Declaration, bs4.CData, bs4.ProcessingInstruction)

RE_XML_START = re.compile(
    b'^(?:(' +
    b'<\\?xml[^>]+?>' +  # ASCII like
    b')|(' +
    re.escape('<?xml'.encode('utf-32-be')) + b'.+?' + re.escape('>'.encode('utf-32-be')) +
    b')|(' +
    re.escape('<?xml'.encode('utf-32-le')) + b'.+?' + re.escape('>'.encode('utf-32-le')) +
    b')|(' +
    re.escape('<?xml'.encode('utf-16-be')) + b'.+?' + re.escape('>'.encode('utf-16-be')) +
    b')|(' +
    re.escape('<?xml'.encode('utf-16-le')) + b'.+?' + re.escape('>'.encode('utf-16-le')) +
    b'))'
)

RE_XML_ENCODE = re.compile(br'''(?i)^<\?xml[^>]*encoding=(['"])(.*?)\1[^>]*\?>''')
RE_XML_ENCODE_U = re.compile(r'''(?i)^<\?xml[^>]*encoding=(['"])(.*?)\1[^>]*\?>''')


class XmlFilter(filters.Filter):
    """Spelling Python."""

    default_capture = ['*|*']

    break_tags = set()

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super().__init__(options, default_encoding)

    def get_default_config(self):
        """Get default configuration."""

        return {
            "comments": True,
            "attributes": [],
            "break_tags": [],
            "ignores": [],
            "captures": self.default_capture,
            "namespaces": {}
        }

    def setup(self):
        """Setup."""

        self.ancestry = []
        self.user_break_tags = set(self.config['break_tags'])
        self.comments = self.config['comments']
        self.attributes = set(self.config['attributes'])
        self.parser = 'xml'
        self.type = 'xml'
        self.ignores = SelectorMatcher(
            self.config['ignores'], self.type, self.config['namespaces']
        )
        self.captures = SelectorMatcher(
            self.config['captures'], self.type, self.config['namespaces']
        )

    def _has_xml_encode(self, content):
        """Check XML encoding."""

        encode = None

        m = RE_XML_START.match(content)
        if m:
            if m.group(1):
                m2 = RE_XML_ENCODE.match(m.group(1))

                if m2:
                    enc = m2.group(2).decode('ascii')

                    try:
                        codecs.getencoder(enc)
                        encode = enc
                    except LookupError:
                        pass
            else:
                if m.group(2):
                    enc = 'utf-32-be'
                    text = m.group(2)
                elif m.group(3):
                    enc = 'utf-32-le'
                    text = m.group(3)
                elif m.group(4):
                    enc = 'utf-16-be'
                    text = m.group(4)
                elif m.group(5):
                    enc = 'utf-16-le'
                    text = m.group(5)
                try:
                    m2 = RE_XML_ENCODE_U.match(text.decode(enc))
                except Exception:  # pragma: no cover
                    m2 = None

                if m2:
                    enc = m2.group(2)

                    try:
                        codecs.getencoder(enc)
                        encode = enc
                    except Exception:
                        pass

        return encode

    def header_check(self, content):
        """Special HTML encoding check."""

        return self._has_xml_encode(content)

    def is_break_tag(self, el):
        """Check if tag is an element we should break on."""

        name = el.name
        return name in self.break_tags or name in self.user_break_tags

    def store_blocks(self, el, blocks, text, is_root):
        """Store the text as desired."""

        if is_root or self.is_break_tag(el):
            content = html.unescape(''.join(text))
            if content:
                blocks.append((content, self.construct_selector(el)))
            text = []
        return text

    def construct_selector(self, el, attr=''):
        """Construct an selector for context."""

        selector = []

        for ancestor in self.ancestry:
            if ancestor is not el:
                if ancestor.name != '[document]':
                    selector.append(ancestor.name)
            elif ancestor.name != '[document]':
                tag = ancestor.name
                prefix = ancestor.prefix
                sel = ''
                if prefix:
                    sel += prefix + '|'
                sel = tag
                if attr:
                    sel += '[%s]' % attr
                selector.append(sel)
        return '>'.join(selector)

    def extract_tag_metadata(self, el):
        """Extract meta data."""

        self.ancestry.append(el)

    def pop_tag_metadata(self):
        """Clear tag metadata."""

        self.ancestry.pop()

    def reset(self):
        """Reset."""

        self.ancestry = []

    def to_text(self, tree, root=False):
        """
        Extract text from tags.

        Skip any selectors specified and include attributes if specified.
        Ignored tags will not have their attributes scanned either.
        """

        self.extract_tag_metadata(tree)

        text = []
        attributes = []
        comments = []
        blocks = []

        if root or not self.ignores.match(tree):
            capture = self.captures.match(tree)
            # Check attributes for normal tags
            if not root and capture:
                for attr in self.attributes:
                    value = tree.attrs.get(attr, '').strip()
                    if value:
                        sel = self.construct_selector(tree, attr=attr)
                        attributes.append((html.unescape(value), sel))

            # Walk children
            for child in tree.children:
                string = str(child).strip()
                is_comment = isinstance(child, bs4.Comment)
                if isinstance(child, bs4.element.Tag):
                    t, b, a, c = self.to_text(child)
                    text.extend(t)
                    attributes.extend(a)
                    comments.extend(c)
                    blocks.extend(b)
                # Get content if not the root and not a comment (unless we want comments).
                elif not isinstance(child, NON_CONTENT) and (not is_comment or self.comments):
                    string = str(child).strip()
                    if string:
                        if is_comment:
                            sel = self.construct_selector(tree) + '<!--comment-->'
                            comments.append((html.unescape(string), sel))
                        elif capture:
                            text.append(string)
                            text.append(' ')

        text = self.store_blocks(tree, blocks, text, root)

        self.pop_tag_metadata()

        if root:
            return blocks, attributes, comments
        else:
            return text, blocks, attributes, comments

    def _filter(self, text, context, encoding):
        """Filter the source text."""

        content = []
        blocks, attributes, comments = self.to_text(bs4.BeautifulSoup(text, self.parser), True)
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

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            text = f.read()
        return self._filter(text, source_file, encoding)

    def sfilter(self, source):
        """Filter."""

        return self._filter(source.text, source.context, source.encoding)


def get_plugin():
    """Return the filter."""

    return XmlFilter
