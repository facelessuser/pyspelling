"""
XML filter.

Detect encoding from XML header.
"""
from __future__ import unicode_literals
from .. import filters
import re
import codecs
import bs4
import soupsieve as sv
from collections import deque, OrderedDict

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

        self.user_break_tags = set()
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

        self.user_break_tags = set(self.config['break_tags'])
        self.comments = self.config['comments']
        self.attributes = set(self.config['attributes'])
        self.parser = 'xml'
        self.type = 'xml'
        ignores = ','.join(self.config['ignores'])
        self.ignores = sv.compile(ignores, self.config['namespaces']) if ignores.strip() else None
        captures = ','.join(self.config['captures'])
        self.captures = sv.compile(captures, self.config['namespaces']) if captures.strip() else None

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

    def format_blocks(self):
        """Format the text as for a block."""

        block_text = []
        for el, text in self._block_text.items():
            content = ''.join(text)
            if content:
                block_text.append((content, self.construct_selector(el)))
        return block_text

    def construct_selector(self, el, attr=''):
        """Construct an selector for context."""

        selector = deque()

        ancestor = el
        while ancestor and ancestor.parent:
            if ancestor is not el:
                selector.appendleft(ancestor.name)
            else:
                tag = ancestor.name
                prefix = ancestor.prefix
                sel = ''
                if prefix:
                    sel += prefix + '|'
                sel = tag
                if attr:
                    sel += '[%s]' % attr
                selector.appendleft(sel)
            ancestor = ancestor.parent
        return '>'.join(selector)

    def extract_tag_metadata(self, el):
        """Extract meta data."""

    def reset(self):
        """Reset."""

    def get_last_descendant(self, node):
        """Get the last descendant."""

        if node.next_sibling is not None:
            last_descendant = node.next_sibling
        else:
            last_child = node
            while isinstance(last_child, bs4.Tag) and last_child.contents:
                last_child = last_child.contents[-1]
            last_descendant = last_child.next_element

        return last_descendant

    def extract_attributes(self, node):
        """Extract attribute values."""

        for attr in self.attributes:
            value = node.attrs.get(attr, '').strip()
            if value:
                sel = self.construct_selector(node, attr=attr)
                self._attributes.append((value, sel))

    def extract_string(self, node, is_comments):
        """Extract string."""

        string = str(node).strip()
        if string:
            if is_comments:
                sel = self.construct_selector(node.parent) + '<!--comment-->'
                self._comments.append((string, sel))
            else:
                self._block_text[self._current_block].append(string)
                self._block_text[self._current_block].append(' ')

    def set_block(self, node, force=False):
        """Set the current block."""

        if not force and node is self._block_stack[-1][1]:
            self._block_stack.pop(-1)
            self._current_block = self._block_stack[-1][0]

        if force or self.is_break_tag(node):
            self._block_stack.append((node, self.get_last_descendant(node)))
            self._block_text[node] = []
            self._current_block = node

    def to_text(self, root):
        """Extract text from the document node."""

        last_capture = None
        last_capture_value = False
        next_good = None

        self._attributes = []
        self._comments = []
        self._block_text = OrderedDict()
        self._block_stack = []
        self.set_block(root, force=True)
        self.extract_tag_metadata(root)

        if not (self.ignores.match(root) if self.ignores else None):
            capture = self.captures.match(root) if self.captures is not None else None
            last_capture = root
            last_capture_value = capture

            if capture:
                self.extract_attributes(root)

            for node in root.descendants:

                if next_good is not None:
                    # We are currently ignoring nodes from an ignored tag.
                    # When we see the first tag that is not a child of the ignored tag,
                    # we can start analyzing tags and text again. Comments are excluded
                    # from ignored, and are captured regardless.
                    if node is not next_good:
                        if self.comments and isinstance(node, bs4.Comment):
                            self.extract_string(node, True)
                        continue
                    next_good = None

                if isinstance(node, bs4.Tag):
                    # Handle tags
                    self.extract_tag_metadata(node)
                    self.set_block(node)

                    if not (self.ignores.match(node) if self.ignores else None):
                        # Handle tags that are not ignored
                        capture = self.captures.match(node) if self.captures is not None else None
                        last_capture = node
                        last_capture_value = capture
                        # Elements that are scheduled to be captured should be checked for attributes to check
                        if capture:
                            self.extract_attributes(node)
                    else:
                        # Handle ignored tags by calculating their last descendant
                        # so we know how long we should ignore nodes
                        next_good = self.get_last_descendant(node)
                        if next_good is None:
                            break
                else:
                    # Handle test nodes: normal text and comments
                    is_comments = isinstance(node, bs4.Comment)
                    if (self.comments and is_comments) or (not is_comments and not isinstance(node, NON_CONTENT)):
                        # Nodes are parsed in order, so sometimes we will descend into another child tag before
                        # all text nodes of the current tag are processed. So we track whether text of the parent
                        # tag should be captured. If we process multiple text nodes of a given tag, we don't
                        # have to recalculate. This allows us to capture text from desired tags.
                        parent = node.parent
                        if is_comments:
                            capture = True
                        elif parent is last_capture:
                            capture = last_capture_value
                        elif not (self.captures.match(parent) if self.captures is not None else None):
                            capture = self.captures.match(parent) if self.captures is not None else None
                            last_capture = parent
                            last_capture_value = capture

                        if capture:
                            self.extract_string(node, is_comments)
        elif self.comments:
            # If the root tag is ignored, but comments is enabled, parse the comments
            for node in root.descendants:
                if isinstance(node, bs4.Comment):
                    self.extract_string(node, True)

        return self.format_blocks(), self._attributes, self._comments

    def _filter(self, text, context, encoding):
        """Filter the source text."""

        content = []
        blocks, attributes, comments = self.to_text(bs4.BeautifulSoup(text, self.parser))
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
