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

MODE = {'html': 'lxml', 'xhtml': 'xml', 'html5': 'html5lib'}

XHTML_NAMESPACE = ('http://www.w3.org/1999/xhtml',)


class HtmlSelector(namedtuple('HtmlSelector', ['tags', 'ids', 'classes', 'attributes'])):
    """Ignore rule."""


class HtmlFilter(xml.XmlFilter):
    """Spelling Python."""

    re_sel = re.compile(
        r'''(?x)
        (?P<not_open>:not\()?(?:                                                    # optinal pseudo selector wrapper
            (?P<class_id>(?:\#|\.)[-\w]+) |                                         #.class and #id
            (?P<ns_tag>(?:(?:[-\w]+|\*)?\|)?(?:[-\w:]+|\*)) |                       # namespace:tag
            \[(?P<ns_attr>(?:(?:[-\w]+|\*)?\|)?[-\w:]+)                             # namespace:attributes
                (?:(?P<cmp>[~^|*$]?=)                                               # compare
                (?P<value>"(\\.|[^\\"]+)*?"|'(\\.|[^\\']+)*?'|[^'"\[\] \t\r\n]+))?  # attribute value
                (?P<i>[ ]+i)?                                                       # case insensitive
            \]
        )(?P<not_close>\))? |                                                       # optional psuedo selector close
        (?P<split>\s*,\s*) |                                                        # split multiple selectors
        .+                                                                          # not proper syntax
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

    default_capture = ['*|*:not(script):not(style)']

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super(HtmlFilter, self).__init__(options, default_encoding)

        self.type = options.get('mode', 'html')
        if self.type not in MODE:
            self.type = 'html'
        self.parser = MODE[self.type]

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

        selectors = []

        for selector in args:
            has_selector = False
            tag = []
            attributes = []
            tag_id = []
            classes = []

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
                            tag.append(xml.SelectorTag('*', None, False))
                        selectors.append(HtmlSelector(tag, tag_id, tuple(classes), tuple(attributes)))
                    has_selector = False
                    tag = []
                    attributes = []
                    tag_id = []
                    classes = []
                    continue
                elif m.group('ns_attr'):
                    attributes.append(self.create_attribute_selector(m, is_not))
                    has_selector = True
                elif m.group('ns_tag'):
                    tag.append(self.parse_tag_pattern(m, is_not))
                    has_selector = True
                elif m.group('class_id'):
                    selector = m.group('class_id')
                    if selector.startswith('.'):
                        classes.append(xml.SelectorString(selector[1:], is_not))
                        has_selector = True
                    else:
                        tag_id.append(xml.SelectorString(selector[1:], is_not))
                        has_selector = True
                else:
                    raise ValueError("Bad selector '{}'".format(m.group(0)))

            if has_selector:
                if not tag:
                    # Implied `*`
                    tag.append(xml.SelectorTag('*', None, False))
                selectors.append(HtmlSelector(tag, tag_id, tuple(classes), tuple(attributes)))

        return selectors

    def get_classes(self, el):
        """Get classes."""

        if self.type != 'xhtml':
            return el.attrs.get('class', [])
        else:
            return [c for c in el.attrs.get('class', '').strip().split(' ') if c]

    def supports_namespaces(self):
        """Check if namespaces are supported in the HTML type."""

        return self.type in ('html5', 'xhtml')

    def get_attribute(self, el, attr, prefix, is_not):
        """Get attribute from element if it exists."""

        value = None
        if self.type == 'xhtml':
            value = super(HtmlFilter, self).get_attribute(el, attr, prefix)
        elif self.supports_namespaces():
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
                if prefix and p and self.selector_equal(prefix != '*' and prefix.lower() != p.lower(), is_not):
                    continue
                # The attribute doesn't match.
                if self.selector_equal(attr.lower() != a.lower(), is_not):
                    continue
                value = v
                break
        else:
            for k, v in el.attrs.items():
                if self.selector_equal(attr.lower() != k.lower(), is_not):
                    continue
                value = v
                break
        return value

    def match_tagname(self, el, tag):
        """Match tag name."""

        return not (
            tag.name and
            self.selector_equal(
                tag.name not in ((el.name.lower() if not self.supports_namespaces() else el.name), '*'),
                tag.is_not
            )
        )

    def match_tag(self, el, tags):
        """Match the tag."""

        has_ns = self.supports_namespaces()
        match = True
        for t in tags:
            # Verify namespace
            if has_ns and not self.match_namespace(el, t):
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
            # Verify id matches
            if selector.ids:
                found = True
                for i in selector.ids:
                    if self.selector_equal(i != el.attrs.get('id', ''), i.is_not):
                        found = False
                        break
                if not found:
                    continue
            # Verify classes match
            if selector.classes:
                current_classes = self.get_classes(el)
                found = True
                for c in selector.classes:
                    if self.selector_equal(c not in current_classes, c.is_not):
                        found = False
                        break
                if not found:
                    continue
            # Verify attribute(s) match
            if not self.match_attributes(el, selector.attributes):
                continue
            match = True
            break
        return match

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

        selector = []
        for ancestor in self.ancestry:
            if ancestor is not el:
                selector.append(ancestor.name)
            else:
                tag = ancestor.name
                prefix = ancestor.prefix
                classes = self.get_classes(ancestor)
                tag_id = ancestor.attrs.get('id', '').strip()
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
                selector.append(sel)
        return ' '.join(selector)


def get_plugin():
    """Return the filter."""

    return HtmlFilter
