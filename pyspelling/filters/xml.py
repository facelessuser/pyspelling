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
from collections import namedtuple

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


class SelectorString(str):
    """String wrapper for selectors."""

    def __new__(cls, string, inverse=False):
        """Construct new string."""

        sel_str = super(SelectorString, cls).__new__(cls, string)
        setattr(sel_str, '_not', inverse)
        return sel_str

    @property
    def is_not(self):
        """Check if is not."""

        return self._not


class Selector(namedtuple('Selector', ['tags', 'attributes'])):
    """Selector."""


class SelectorTag(namedtuple('SelectorTag', ['name', 'prefix', 'is_not'])):
    """Selector tag."""


class SelectorAttribute(namedtuple('AttrRule', ['attribute', 'prefix', 'pattern', 'is_not'])):
    """Selector attribute rule."""


class XmlFilter(filters.Filter):
    """Spelling Python."""

    re_sel = re.compile(
        r'''(?x)
        (?P<not_open>:not\()?(?:                                                      # optinal pseudo selector wrapper
            (?P<ns_tag>(?:(?:[-\w.]+|\*)?\|)?(?:[-\w:.]+|\*)) |                       # namespace:tag
            \[(?P<ns_attr>(?:(?:[-\w]+|\*)\|)?[-\w:.]+)                               # namespace:attributes
                (?:(?P<cmp>[~^|*$]?=)                                                 # compare
                (?P<value>"(\\.|[^\\"]+)*?"|'(?:\\.|[^\\']+)*?'|[^'"\[\] \t\r\n]+))?  # attribute value
                (?P<i>[ ]+i)?                                                         # case insensitive
            \]
        )(?P<not_close>\))? |                                                         # optional psuedo selector close
        (?P<split>\s*,\s*) |                                                          # Split for multiple selectors
        .+                                                                            # not proper syntax
        '''
    )

    default_capture = ['*|*']

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        self.ancestry = []
        self.comments = options.get('comments', True) is True
        self.attributes = set(options.get('attributes', []))
        self.parser = 'xml'
        self.type = 'xml'
        self.ignores = self.process_selectors(*options.get('ignores', []))
        self.captures = self.process_selectors(*options.get('captures', self.default_capture))
        self.namespaces = options.get('namespaces', {})
        super(XmlFilter, self).__init__(options, default_encoding)

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

    def get_namespace(self, el):
        """Get the namespace for the element."""

        namespace = ''
        ns = el.namespace
        if ns:
            namespace = ns
        return namespace

    def create_attribute_selector(self, m, is_not):
        """Create attribute selector from the returned regex match."""

        flags = re.I if m.group('i') else 0
        parts = [a.strip() for a in m.group('ns_attr').split('|')]
        ns = ''
        if len(parts) > 1:
            ns = parts[0]
            attr = parts[1]
        else:
            attr = parts[0]
        op = m.group('cmp')
        if op:
            value = m.group('value')[1:-1] if m.group('value').startswith('"') else m.group('value')
        else:
            value = None
        if not op:
            # Attribute name
            pattern = None
        elif op.startswith('^'):
            # Value start with
            pattern = re.compile(r'^%s.*' % re.escape(value), flags)
        elif op.startswith('$'):
            # Value ends with
            pattern = re.compile(r'.*?%s$' % re.escape(value), flags)
        elif op.startswith('*'):
            # Value contains
            pattern = re.compile(r'.*?%s.*' % re.escape(value), flags)
        elif op.startswith('~'):
            # Value contains word within space separated list
            pattern = re.compile(r'.*?(?:(?<=^)|(?<= ))%s(?=(?:[ ]|$)).*' % re.escape(value), flags)
        elif op.startswith('|'):
            # Value starts with word in dash separated list
            pattern = re.compile(r'^%s(?=-).*' % re.escape(value), flags)
        else:
            # Value matches
            pattern = re.compile(r'^%s$' % re.escape(value), flags)
        return SelectorAttribute(attr, ns, pattern, is_not)

    def parse_tag_pattern(self, m, is_not):
        """Parse tag pattern from regex match."""

        parts = m.group('ns_tag').split('|')
        if len(parts) > 1:
            prefix = parts[0]
            tag = parts[1]
        else:
            tag = parts[0]
            prefix = None
        return SelectorTag(tag, prefix, is_not)

    def process_selectors(self, *args):
        """
        Process selectors.

        We do our own selectors as BeautifulSoup4 has some annoying quirks,
        and we don't really need to do nth selectors or siblings or
        descendants etc.
        """

        selectors = []

        for selector in args:
            has_selector = False
            tag = []
            attributes = []

            for m in self.re_sel.finditer(selector):
                # Track if this is `not` and fail if syntax is broken
                if m.group('not_open') and m.group('not_close'):
                    is_not = True
                elif m.group('not_open') or m.group('not_close'):
                    raise ValueError("Bad selector '{}'".format(m.group(0)))
                else:
                    is_not = False

                # Handle parts
                if m.group('split'):
                    if has_selector:
                        if not tag:
                            # Implied `*`
                            tag.append(SelectorTag('*', None, False))
                        selectors.append(Selector(tag, tuple(attributes)))
                    has_selector = False
                    tag = []
                    attributes = []
                    continue
                elif m.group('ns_attr'):
                    attributes.append(self.create_attribute_selector(m, is_not))
                    has_selector = True
                elif m.group('ns_tag'):
                    tag.append(self.parse_tag_pattern(m, is_not))
                    has_selector = True
                else:
                    raise ValueError("Bad selector '{}'".format(m.group(0)))

            if has_selector:
                if not tag:
                    # Implied `*`
                    tag.append(SelectorTag('*', None, False))
                selectors.append(Selector(tag, tuple(attributes)))

        return selectors

    def get_attribute(self, el, attr, prefix, is_not):
        """Get attribute from element if it exists."""

        value = None
        # If we have not defined namespaces, we can't very well find them, so don't bother trying.
        if prefix and self.selector_equal(prefix not in self.namespaces and prefix != '*', is_not):
            return None

        for k, v in el.attrs.items():
            parts = k.split(':', 1)
            if len(parts) > 1:
                if not parts[0]:
                    a = k
                    p = ''
                else:
                    p = parts[0]
                    a = parts[1]
            else:
                p = ''
                a = k
            # Can't match a prefix attribute as we haven't specified one to match
            if self.selector_equal(not prefix and p, is_not):
                continue
            # We can't match our desired prefix attribute as the attribute doesn't have a prefix
            if prefix and not p and self.selector_equal(prefix != '*', is_not):
                continue
            # The prefix doesn't match
            if prefix and p and self.selector_equal(prefix != '*' and prefix != p, is_not):
                continue
            # The attribute doesn't match.
            if self.selector_equal(attr != a, is_not):
                continue
            value = v
            break
        return value

    def selector_equal(self, value, is_not):
        """Evaluate if equal, but apply inverse logic if in `:not`."""

        return not bool(value) if is_not else bool(value)

    def match_namespace(self, el, tag):
        """Match the namespace of the element."""

        match = True
        namespace = self.get_namespace(el)
        default_namespace = self.namespaces.get('')
        # We must match the default namespace if one is not provided
        if tag.prefix is None and (default_namespace is not None and namespace != default_namespace):
            match = False
        # If we specified `|tag`, we must not have a namespace.
        elif (tag.prefix is not None and tag.prefix == '' and self.selector_equal(namespace, tag.is_not)):
            match = False
        # Verify prefix matches
        elif (
            tag.prefix and
            self.selector_equal(tag.prefix != '*' and namespace != self.namespaces.get(tag.prefix, ''), tag.is_not)
        ):
            match = False
        return match

    def match_attributes(self, el, attributes):
        """Match attributes."""

        match = True
        if attributes:
            for a in attributes:
                value = self.get_attribute(el, a.attribute, a.prefix, a.is_not)
                if isinstance(value, list):
                    value = ' '.join(value)
                if a.pattern is None and self.selector_equal(value is None, a.is_not):
                    match = False
                    break
                elif not a.is_not and a.pattern is not None and value is None:
                    match = False
                    break
                elif a.pattern is None:
                    continue
                elif self.selector_equal(value is None or a.pattern.match(value) is None, a.is_not):
                    match = False
                    break
        return match

    def match_tagname(self, el, tag):
        """Match tag name."""

        return not (tag.name and self.selector_equal(tag.name not in (el.name, '*'), tag.is_not))

    def match_tag(self, el, tags):
        """Match the tag."""

        match = True
        for t in tags:
            # Verify namespace
            if not self.match_namespace(el, t):
                match = False
                break
            if not self.match_tagname(el, t):
                match = False
                break
        return match

    def match_selectors(self, el, selectors):
        """Check if element matches one of the selectors."""

        match = False
        for selector in selectors:
            # Verify tag matches
            if not self.match_tag(el, selector.tags):
                continue
            # Verify attribute(s) match
            if not self.match_attributes(el, selector.attributes):
                continue
            match = True
            break
        return match

    def store_blocks(self, el, blocks, text, is_root):
        """Store the text as desired."""

        if is_root:
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
                selector.append(ancestor.name)
            else:
                tag = ancestor.name
                prefix = ancestor.prefix
                sel = ''
                if prefix:
                    sel += prefix + '|'
                sel = tag
                if attr:
                    sel += '[%s]' % attr
                selector.append(sel)
        return ' '.join(selector)

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

        if root or not self.match_selectors(tree, self.ignores):
            capture = self.match_selectors(tree, self.captures)
            # Check attributes for normal tags
            if not root and capture:
                for attr in self.attributes:
                    value = tree.attrs.get(attr, '').strip()
                    if value:
                        sel = self.construct_selector(tree, attr=attr)
                        attributes.append((html.unescape(value), sel))

            # Walk children
            for child in list(tree):
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
