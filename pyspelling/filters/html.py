"""
HTML filter.

Detect encoding from HTML header.
"""
from __future__ import unicode_literals
import re
import codecs
import html
from . import xml
from ..util.css_selectors import SelectorMatcher, lower
from collections import deque

RE_HTML_ENCODE = re.compile(
    br'''(?xi)
    <\s*meta(?!\s*(?:name|value)\s*=)(?:[^>]*?content\s*=[\s"']*)?(?:[^>]*?)[\s"';]*charset\s*=[\s"']*([^\s"'/>]*)
    '''
)

MODE = {'html': 'lxml', 'xhtml': 'xml', 'html5': 'html5lib'}


class HtmlFilter(xml.XmlFilter):
    """Spelling Python."""

    break_tags = {
        # Block level elements (and other blockish elements)
        'address', 'article', 'aside', 'blockquote', 'details', 'dialog', 'dd',
        'div', 'dl', 'dt'
        'fieldset', 'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3',
        'h4', 'h5', 'h6', 'header', 'hgroup', 'hr', 'li', 'main', 'menu', 'nav', 'ol', 'p', 'pre',
        'section', 'table', 'ul',
        'canvas', 'group', 'iframe', 'math', 'noscript', 'output',
        'script', 'style', 'table', 'video', 'body', 'head'
    }

    default_capture = ['*|*:not(script, style)']

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super().__init__(options, default_encoding)

    def get_default_config(self):
        """Get default configuration."""

        return {
            "comments": True,
            "mode": "html",
            "attributes": [],
            "break_tags": [],
            "ignores": [],
            "captures": self.default_capture,
            "namespaces": {}
        }

    def validate_options(self, k, v):
        """Validate options."""

        super().validate_options(k, v)
        if k == 'mode' and v not in MODE:
            raise ValueError("{}: '{}' is not a valid value for '{}'".format(self.__class__.__name, v, k))

    def setup(self):
        """Setup."""

        self.user_break_tags = set(self.config['break_tags'])
        self.comments = self.config.get('comments', True) is True
        self.attributes = set(self.config['attributes'])
        self.type = self.config['mode']
        if self.type not in MODE:
            self.type = 'html'
        self.parser = MODE[self.type]
        self.ignores = SelectorMatcher(
            ','.join(self.config['ignores']), self.type, self.config['namespaces']
        )
        self.captures = SelectorMatcher(
            ','.join(self.config['captures']), self.type, self.config['namespaces']
        )

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

    def is_break_tag(self, el):
        """Check if tag is an element we should break on."""

        name = lower(el.name) if self.type != 'xhtml' else el.name
        return name in self.break_tags or name in self.user_break_tags

    def get_classes(self, el):
        """Get classes."""

        if self.type != 'xhtml':
            return el.attrs.get('class', [])
        else:
            return [c for c in el.attrs.get('class', '').strip().split(' ') if c]

    def store_blocks(self, el, blocks, text, force_root):
        """Store the text as desired."""

        if force_root or el.parent is None or self.is_break_tag(el):
            content = html.unescape(''.join(text))
            if content:
                blocks.append((content, self.construct_selector(el)))
            text = []
        return text

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
                selector.appendleft(sel)
            ancestor = ancestor.parent
        return '>'.join(selector)


def get_plugin():
    """Return the filter."""

    return HtmlFilter
