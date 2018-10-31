"""
HTML filter.

Detect encoding from HTML header.
"""
from __future__ import unicode_literals
import re
import codecs
import html
from . import xml
from collections import namedtuple

RE_HTML_ENCODE = re.compile(
    br'''(?xi)
    <\s*meta(?!\s*(?:name|value)\s*=)(?:[^>]*?content\s*=[\s"']*)?(?:[^>]*?)[\s"';]*charset\s*=[\s"']*([^\s"'/>]*)
    '''
)

MODE = {'html': 'lxml', 'xhtml': 'xml', 'html5lib': 'html5lib'}


class HtmlSelector(namedtuple('IgnoreRule', ['tag', 'namespace', 'id', 'classes', 'attributes'])):
    """Ignore rule."""


class HtmlFilter(xml.XmlFilter):
    """Spelling Python."""

    re_sel = re.compile(
        r'''(?x)
        (?P<class_id>(?:\#|\.)[-\w]+) |                         #.class and #id
        (?P<ns_tag>(?:(?:[-\w]+|\*)\|)?(?:[-\w:]+|\*)|\|\*) |   # namespace:tag
        \[(?P<attr>[\w\-:]+)                                    # attributes
            (?:(?P<cmp>[~^|*$]?=)                               # compare
            (?P<value>\"[^"]+\"|'[^']'|[^'"\[\] \t\r\n]+))?     # attribute value
            (?P<i>[ ]+i)?                                       # case insensitive
        \] |
        .+
        '''
    )

    block_tags = [
        # Block level elements (and other blockish elements)
        'address', 'article', 'aside', 'blockquote', 'details', 'dialog', 'dd',
        'div', 'dl', 'dt'
        'fieldset', 'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3',
        'h4', 'h5', 'h6', 'header', 'hgroup', 'hr', 'li', 'main', 'menu', 'nav', 'ol', 'p', 'pre',
        'section', 'table', 'ul',
        'canvas', 'group', 'iframe', 'math', 'noscript', 'output',
        'script', 'style', 'table', 'video', 'body', 'head'
    ]

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super(HtmlFilter, self).__init__(options, default_encoding)

        self.mode = MODE.get(options.get('mode', 'html'), 'lxml')
        self.prefix = 'html' if self.mode != 'xml' else 'xhtml'

    def header_check(self, content):
        """Special HTML encoding check."""

        encode = None

        # Look for meta charset
        m = RE_HTML_ENCODE.search(content)
        if m:
            enc = m.group(1).decode('ascii')

            try:
                codecs.getencoder(enc)
                encode = enc
            except LookupError:
                pass
        else:
            encode = self._has_xml_encode(content)
        return encode

    def is_block(self, el):
        """Check if tag is a block element."""

        return el.name.lower() in self.block_tags

    def process_selectors(self, *args):
        """
        Process selectors.

        We do our own selectors as BeautifulSoup4 has some annoying quirks,
        and we don't really need to do nth selectors or siblings or
        descendants etc.
        """

        selectors = [
            HtmlSelector('style', None, None, tuple(), tuple()),
            HtmlSelector('script', None, None, tuple(), tuple()),
        ]

        for selector in args:
            has_selector = False
            tag = None
            attributes = []
            namespace = None
            tag_id = None
            classes = set()

            for m in self.re_sel.finditer(selector):
                flags = re.I if m.group('i') else 0
                if m.group('attr'):
                    attr = m.group('attr')
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
                    attributes.append(xml.SelectorAttribute(attr, pattern))
                    has_selector = True
                elif m.group('class_id'):
                    selector = m.group('class_id')
                    if selector.startswith('.'):
                        classes.add(selector[1:])
                        has_selector = True
                    elif tag_id is None:
                        tag_id = selector[1:]
                        has_selector = True
                elif m.group('ns_tag'):
                    selector = m.group('ns_tag')
                    parts = selector.split('|')
                    if tag is None:
                        if len(parts) > 1:
                            namespace = parts[0]
                            tag = parts[1]
                        else:
                            tag = parts[0]
                        has_selector = True
                    else:
                        raise ValueError('Bad selector!')
                else:
                    raise ValueError('Bad selector!')

            if has_selector:
                selectors.append(HtmlSelector(tag, namespace, tag_id, tuple(classes), tuple(attributes)))

        return selectors

    def get_classes(self, el):
        """Get classes."""

        if self.mode != 'xml':
            return el.attrs.get('class', [])
        else:
            return [c for c in el.attrs.get('class', '').strip().split(' ') if c]

    def get_attribute(self, el, attr):
        """Get attribute from element if it exists."""

        if self.mode != 'xml':
            # Case insensitive
            value = None
            for k, v in el.attrs.items():
                if attr.lower() == k.lower():
                    value = v
                    break
        else:
            value = el.attrs.get(attr)
            # Normalize class for XHTML like HTML
            if attr.lower() == 'class' and isinstance(value, str):
                value = [c for c in value.strip().split(' ') if c]
        return value

    def skip_tag(self, el):
        """Determine if tag should be skipped."""

        skip = False
        for selector in self.selectors:
            if (
                selector.namespace is not None and
                selector.namespace is not '*' and
                (
                    (el.namespace is None and selector.namespace) or
                    (el.namespace is not None and el.namespace != selector.namespace)
                )
            ):
                continue
            if selector.tag and selector.tag not in ((el.name.lower() if self.mode != 'xml' else el.name), '*'):
                continue
            if selector.id and selector.id != el.attrs.get('id', ''):
                continue
            if selector.classes:
                current_classes = self.get_classes(el)
                found = True
                for c in selector.classes:
                    if c not in current_classes:
                        found = False
                        break
                if not found:
                    continue
            if selector.attributes:
                found = True
                for a in selector.attributes:
                    value = self.get_attribute(el, a.attribute)
                    if isinstance(value, list):
                        value = ' '.join(value)
                    if not value:
                        found = False
                        break
                    elif a.pattern is None:
                        continue
                    elif a.pattern.match(value) is None:
                        found = False
                        break
                if not found:
                    continue
            skip = True
            break
        return skip

    def store_blocks(self, el, blocks, text, is_root):
        """Store the text as desired."""

        if is_root or self.is_block(el):
            content = html.unescape(''.join(text))
            if content:
                blocks.append((content, self.construct_selector(el)))
            text = []
        return text

    def construct_selector(self, el, attr=''):
        """Construct an selector for context."""

        tag = el.name
        prefix = el.prefix
        classes = self.get_classes(el)
        tag_id = el.attrs.get('id', '').strip()
        sel = ''
        if prefix:
            sel += prefix + '|'
        sel += tag
        if tag_id:
            sel += '#' + tag_id
        if classes:
            sel += '.' + '.'.join(classes)
        if attr:
            sel += '[%s]' % attr
        return sel


def get_plugin():
    """Return the filter."""

    return HtmlFilter
