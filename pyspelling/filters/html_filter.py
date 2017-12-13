"""HTML filter."""
from __future__ import unicode_literals
from .. import filters
from collections import namedtuple
import bs4
import re
from .. import util
from html.parser import HTMLParser

RE_SELECTOR = re.compile(r'''(\#|\.)?[-\w]+|\*|\[([\w\-:]+)(?:([~^|*$]?=)(\"[^"]+\"|'[^']'|[^'"\[\]]+))?\]''')


class Selector(namedtuple('IgnoreRule', ['tag', 'id', 'classes', 'attributes'])):
    """Ignore rule."""


class SelectorAttribute(namedtuple('AttrRule', ['attribute', 'pattern'])):
    """Selector attribute rule."""


class HTMLFilter(filters.Filter):
    """HTML filter."""

    def __init__(self, options):
        """Initialize."""

        self.html_parser = HTMLParser()
        self.attributes = set(options.get('attributes', []))
        self.selectors = self.process_selectors(*options.get('ignores', []))

    def process_selectors(self, *args):
        """
        Process selectors.

        We do our own selectors as BeautifulSoup4 has some annoying quirks,
        and we don't really need to do nth selectors or siblings or
        descendants etc.
        """

        selectors = [
            Selector('style', None, tuple(), tuple()),
            Selector('script', None, tuple(), tuple()),
        ]

        for selector in args:
            tag = None
            tag_id = None
            classes = set()
            attributes = []

            for m in RE_SELECTOR.finditer(selector):
                if m.group(2):
                    attr = m.group(2).lower()
                    op = m.group(3)
                    if op:
                        value = m.group(4)[1:-1] if m.group(4).startswith('"') else m.group(4)
                    else:
                        value = None
                    if not op:
                        # Attribute name
                        pattern = None
                    elif op.startswith('^'):
                        # Value start with
                        pattern = re.compile(r'^%s.*' % re.escape(value))
                    elif op.startswith('$'):
                        # Value ends with
                        pattern = re.compile(r'.*?%s$' % re.escape(value))
                    elif op.startswith('*'):
                        # Value contains
                        pattern = re.compile(r'.*?%s.*' % re.escape(value))
                    elif op.startswith('~'):
                        # Value contains word within space separated list
                        pattern = re.compile(r'.*?(?:(?<=^)|(?<= ))%s(?=(?:[ ]|$)).*' % re.escape(value))
                    elif op.startswith('|'):
                        # Value starts with word in dash separated list
                        pattern = re.compile(r'^%s(?=-).*' % re.escape(value))
                    else:
                        # Value matches
                        pattern = re.compile(r'^%s$' % re.escape(value))
                    attributes.append(SelectorAttribute(attr, pattern))
                else:
                    selector = m.group(0).lower()
                    if selector.startswith('.'):
                        classes.add(selector[1:].lower())
                    elif selector.startswith('#') and tag_id is None:
                        tag_id = selector[1:]
                    elif tag is None:
                        tag = selector
                    else:
                        raise ValueError('Bad selector!')

            if tag or tag_id or classes:
                selectors.append(Selector(tag, tag_id, tuple(classes), tuple(attributes)))

        return selectors

    def skip_tag(self, el):
        """Determine if tag should be skipped."""

        skip = False
        for selector in self.selectors:
            if selector.tag and selector.tag not in (el.name.lower(), '*'):
                continue
            if selector.id and selector.id != el.attrs.get('id', '').lower():
                continue
            if selector.classes:
                current_classes = [c.lower() for c in el.attrs.get('class', [])]
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
                    value = el.attrs.get(a.attribute)
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

    def html_to_text(self, tree, root=True):
        """
        Parse the HTML creating a buffer with each tags content.

        Skip any selectors specified and include attributes if specified.
        Ignored tags will not have their attributes scanned either.
        """

        text = []
        attributes = []

        if not self.skip_tag(tree):
            for attr in self.attributes:
                value = tree.attrs.get(attr, '').strip()
                if value:
                    attributes.append(value)

            for child in tree:
                if isinstance(child, bs4.element.Tag):
                    if child.contents:
                        t, a = (self.html_to_text(child, False))
                        text.extend(t)
                        attributes.extend(a)
                else:
                    string = util.ustr(child).strip()
                    if string:
                        text.append(util.ustr(child))

        if root:
            return self.html_parser.unescape(' '.join(' '.join(text), ' '.join(attributes)))

        return text, attributes

    def filter(self, text):
        """Filter the text."""

        return self.html_to_text(bs4.BeautifulSoup(text, "html5lib").html)


def get_filter():
    """Return the filter."""

    return HTMLFilter
