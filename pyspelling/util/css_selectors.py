"""CSS selector matcher."""
import re
from collections import namedtuple
import bs4

TAG = bs4.element.Tag

CSS_ESCAPES = r'(?:\\[a-fA-F0-9]{1,6}[ ]?|\\.)'
RE_ESC = re.compile(r'(?:(\\[a-fA-F0-9]{1,6}[ ]?)|(\\.))')

RE_HTML_SEL = re.compile(
    r'''(?x)
    (?P<pseudo_open>:(?:not|matches|is)\() |                                      # optinal pseudo selector wrapper
    (?P<class_id>(?:\#|\.)(?:[-\w]|{esc})+) |                                     #.class and #id
    (?P<ns_tag>(?:(?:(?:[-\w]|{esc})+|\*)?\|)?(?:(?:[-\w]|{esc})+|\*)) |          # namespace:tag
    \[(?P<ns_attr>(?:(?:(?:[-\w]|{esc})+|\*)?\|)?(?:[-\w]|{esc})+)                # namespace:attributes
    (?:(?P<cmp>[~^|*$]?=)                                                         # compare
    (?P<value>"(\\.|[^\\"]+)*?"|'(\\.|[^\\']+)*?'|(?:[^'"\[\] \t\r\n]|{esc})+))?  # attribute value
    (?P<i>[ ]+i)? \] |                                                            # case insensitive
    (?P<pseudo_close>\)) |                                                        # optional pseudo selector close
    (?P<split>\s*?(?P<relation>[,+>~]|[ ](?![,+>~]))\s*) |                        # split multiple selectors
    (?P<invalid>).+                                                               # not proper syntax
    '''.format(**{'esc': CSS_ESCAPES})
)

RE_XML_SEL = re.compile(
    r'''(?x)
    (?P<pseudo_open>:(?:not|matches|is)\() |                                        # optinal pseudo selector wrapper
    (?P<ns_tag>(?:(?:(?:[-\w.]|{esc})+|\*)?\|)?(?:(?:[-\w.]|{esc})+|\*)) |          # namespace:tag
    \[(?P<ns_attr>(?:(?:(?:[-\w]|{esc})+|\*)\|)?(?:[-\w.]|{esc})+)                  # namespace:attributes
    (?:(?P<cmp>[~^|*$]?=)                                                           # compare
    (?P<value>"(\\.|[^\\"]+)*?"|'(?:\\.|[^\\']+)*?'|(?:[^'"\[\] \t\r\n]|{esc})+))?  # attribute value
    (?P<i>[ ]+i)?\] |                                                               # case insensitive
    (?P<pseudo_close>\)) |                                                          # optional pseudo selector close
    (?P<split>\s*?(?P<relation>[,+>~]|[ ](?![,+>~]))\s*) |                          # Split for multiple selectors
    (?P<invalid>.+)                                                                 # not proper syntax
    '''.format(**{'esc': CSS_ESCAPES})
)

MODES = ('xml', 'html', 'html5', 'xhtml')

LC_A = ord('a')
LC_Z = ord('z')
UC_A = ord('A')
UC_Z = ord('Z')

# Relationships
REL_NONE = ','
REL_PARENT = ' '
REL_CLOSE_PARENT = '>'
REL_SIBLING = '~'
REL_CLOSE_SIBLING = '+'


def unescape(string):
    """Unescape CSS value."""

    def replace(m):
        """Replace with the appropriate substitute."""

        return chr(int(m.group(1)[1:], 16)) if m.group(1) else m.group(2)[1:]

    return RE_ESC.sub(replace, string)


def lower(string):
    """Lower."""

    new_string = []
    for c in string:
        o = ord(c)
        new_string.append(chr(o + 32) if UC_A <= o <= UC_Z else c)
    return ''.join(new_string)


def upper(string):  # pragma: no cover
    """Lower."""

    new_string = []
    for c in string:
        o = ord(c)
        new_string.append(chr(o - 32) if LC_A <= o <= LC_Z else c)
    return ''.join(new_string)


class Selector(
    namedtuple('HtmlSelector', ['tags', 'ids', 'classes', 'attributes', 'selectors', 'is_not', 'relation', 'rel_type'])
):
    """CSS selector."""


class SelectorTag(namedtuple('SelectorTag', ['name', 'prefix'])):
    """Selector tag."""


class SelectorAttribute(namedtuple('AttrRule', ['attribute', 'prefix', 'pattern'])):
    """Selector attribute rule."""


class SelectorMatcher:
    """Match tags in Beautiful Soup with CSS selectors."""

    def __init__(self, selectors, mode='html', namespaces=None):
        """Initialize."""

        self.mode = mode
        self.re_sel = RE_HTML_SEL if self.mode != 'xml' else RE_XML_SEL
        self.namespaces = namespaces if namespaces else {}
        self.selectors = self.process_selectors(*selectors)

    def get_namespace(self, el):
        """Get the namespace for the element."""

        namespace = ''
        ns = el.namespace
        if ns:
            namespace = ns
        return namespace

    def supports_namespaces(self):
        """Check if namespaces are supported in the HTML type."""

        return self.mode in ('html5', 'xhtml', 'xml')

    def is_xml(self):
        """Check if document is an XML type."""

        return self.mode in ('xml', 'xhtml')

    def create_attribute_selector(self, m):
        """Create attribute selector from the returned regex match."""

        flags = re.I if m.group('i') else 0
        parts = [unescape(a.strip()) for a in m.group('ns_attr').split('|')]
        ns = ''
        if len(parts) > 1:
            ns = parts[0]
            attr = parts[1]
        else:
            attr = parts[0]
        op = m.group('cmp')
        if op:
            value = unescape(m.group('value')[1:-1] if m.group('value').startswith(('"', "'")) else m.group('value'))
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
            pattern = re.compile(r'^%s(?:-.*)?$' % re.escape(value), flags)
        else:
            # Value matches
            pattern = re.compile(r'^%s$' % re.escape(value), flags)
        return SelectorAttribute(attr, ns, pattern)

    def parse_tag_pattern(self, m):
        """Parse tag pattern from regex match."""

        parts = [unescape(x) for x in m.group('ns_tag').split('|')]
        if len(parts) > 1:
            prefix = parts[0]
            tag = parts[1]
        else:
            tag = parts[0]
            prefix = None
        return SelectorTag(tag, prefix)

    def parse_selectors(self, iselector, is_pseudo=False, is_not=False, relation=None):
        """Parse selectors."""

        selectors = []
        has_selector = False
        tag = []
        attributes = []
        tag_id = []
        classes = []
        sub_selectors = []
        closed = False
        is_html = self.mode != 'xml'

        try:
            while True:
                m = next(iselector)

                # Handle parts
                if m.group('pseudo_open'):
                    if is_pseudo and is_not:
                        raise ValueError("Pseudo-elements cannot be represented by the negation pseudo-class")
                    sub_selectors.extend(self.parse_selectors(iselector, True, m.group('pseudo_open')[1:-1] == 'not'))
                    has_selector = True
                elif m.group('pseudo_close'):
                    if is_pseudo:
                        closed = True
                        break
                    else:
                        raise ValueError("Bad selector '{}'".format(m.group(0)))
                elif m.group('split'):
                    if not has_selector:
                        raise ValueError("Cannot start selector with '{}'".format(m.group('relation')))
                    if m.group('relation') == REL_NONE:
                        if not tag and not is_pseudo:
                            # Implied `*`
                            tag.append(SelectorTag('*', None))
                        selectors.append(
                            Selector(
                                tag, tag_id, tuple(classes), tuple(attributes), sub_selectors, is_not, relation, None
                            )
                        )
                    else:
                        relation = Selector(
                            tag, tag_id, tuple(classes), tuple(attributes),
                            sub_selectors, False, relation, m.group('relation')
                        )
                    has_selector = False
                    tag = []
                    attributes = []
                    tag_id = []
                    classes = []
                    sub_selectors = []
                    continue
                elif m.group('ns_attr'):
                    attributes.append(self.create_attribute_selector(m))
                    has_selector = True
                elif m.group('ns_tag'):
                    tag.append(self.parse_tag_pattern(m))
                    has_selector = True
                elif is_html and m.group('class_id'):
                    selector = m.group('class_id')
                    if selector.startswith('.'):
                        classes.append(unescape(selector[1:]))
                        has_selector = True
                    else:
                        tag_id.append(unescape(selector[1:]))
                        has_selector = True
                elif m.group('invalid'):
                    raise ValueError("Bad selector '{}'".format(m.group(0)))
        except StopIteration:
            pass

        if is_pseudo and not closed:
            raise ValueError("Unclosed `:pseudo()`")

        if has_selector:
            if not tag and not is_pseudo:
                # Implied `*`
                tag.append(SelectorTag('*', None))
            selectors.append(
                Selector(tag, tag_id, tuple(classes), tuple(attributes), sub_selectors, is_not, relation, None)
            )

        return selectors

    def process_selectors(self, *args):
        """
        Process selectors.

        We do our own selectors as BeautifulSoup4 has some annoying quirks,
        and we don't really need to do nth selectors or siblings or
        descendants etc.
        """

        selectors = []

        for selector in args:
            iselector = self.re_sel.finditer(selector)
            selectors.extend(self.parse_selectors(iselector))
        return selectors

    def get_attribute(self, el, attr, prefix):
        """Get attribute from element if it exists."""

        value = None
        is_xml = self.is_xml()
        if self.supports_namespaces():
            value = None
            # If we have not defined namespaces, we can't very well find them, so don't bother trying.
            if prefix and prefix not in self.namespaces and prefix != '*':
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
                if not prefix and p:
                    continue
                # We can't match our desired prefix attribute as the attribute doesn't have a prefix
                if prefix and not p and prefix != '*':
                    continue
                if is_xml:
                    # The prefix doesn't match
                    if prefix and p and prefix != '*' and prefix != p:
                        continue
                    # The attribute doesn't match.
                    if attr != a:
                        continue
                else:
                    # The prefix doesn't match
                    if prefix and p and prefix != '*' and lower(prefix) != lower(p):
                        continue
                    # The attribute doesn't match.
                    if lower(attr) != lower(a):
                        continue
                value = v
                break
        else:
            for k, v in el.attrs.items():
                if lower(attr) != lower(k):
                    continue
                value = v
                break
        return value

    def get_classes(self, el):
        """Get classes."""

        if self.mode not in ('xhtml', 'xml'):
            return el.attrs.get('class', [])
        else:
            return [c for c in el.attrs.get('class', '').strip().split(' ') if c]

    def match_namespace(self, el, tag):
        """Match the namespace of the element."""

        match = True
        namespace = self.get_namespace(el)
        default_namespace = self.namespaces.get('')
        # We must match the default namespace if one is not provided
        if tag.prefix is None and (default_namespace is not None and namespace != default_namespace):
            match = False
        # If we specified `|tag`, we must not have a namespace.
        elif (tag.prefix is not None and tag.prefix == '' and namespace):
            match = False
        # Verify prefix matches
        elif (
            tag.prefix and
            tag.prefix != '*' and namespace != self.namespaces.get(tag.prefix, '')
        ):
            match = False
        return match

    def match_attributes(self, el, attributes):
        """Match attributes."""

        match = True
        if attributes:
            for a in attributes:
                value = self.get_attribute(el, a.attribute, a.prefix)
                if isinstance(value, list):
                    value = ' '.join(value)
                if a.pattern is None and value is None:
                    match = False
                    break
                elif a.pattern is not None and value is None:
                    match = False
                    break
                elif a.pattern is None:
                    continue
                elif value is None or a.pattern.match(value) is None:
                    match = False
                    break
        return match

    def match_tagname(self, el, tag):
        """Match tag name."""

        return not (
            tag.name and
            tag.name not in ((lower(el.name) if not self.is_xml() else el.name), '*')
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

    def match_relations(self, el, relation):
        """Match relationship to other elements."""

        found = False
        if relation.rel_type == REL_PARENT:
            parent = el.parent
            while not found and parent:
                found = self.match_selectors(parent, [relation])
                parent = parent.parent
        elif relation.rel_type == REL_CLOSE_PARENT:
            parent = el.parent
            if parent:
                found = self.match_selectors(parent, [relation])
        elif relation.rel_type == REL_SIBLING:
            sibling = el.previous_element
            while not found and sibling:
                if not isinstance(sibling, TAG):
                    sibling = sibling.previous_element
                    continue
                found = self.match_selectors(sibling, [relation])
                sibling = sibling.previous_element
        elif relation.rel_type == REL_CLOSE_SIBLING:
            sibling = el.previous_element
            while sibling and not isinstance(sibling, TAG):
                sibling = sibling.previous_element
            if sibling and isinstance(sibling, TAG):
                found = self.match_selectors(sibling, [relation])
        return found

    def match_id(self, el, ids):
        """Match element's ID."""

        found = True
        for i in ids:
            if i != el.attrs.get('id', ''):
                found = False
                break
        return found

    def match_classes(self, el, classes):
        """Match element's classes."""

        current_classes = self.get_classes(el)
        found = True
        for c in classes:
            if c not in current_classes:
                found = False
                break
        return found

    def match_selectors(self, el, selectors):
        """Check if element matches one of the selectors."""

        match = False
        is_html = self.mode != 'xml'
        for selector in selectors:
            match = selector.is_not
            # Verify tag matches
            if not self.match_tag(el, selector.tags):
                continue
            # Verify id matches
            if is_html and selector.ids and not self.match_id(el, selector.ids):
                continue
            # Verify classes match
            if is_html and selector.classes and not self.match_classes(el, selector.classes):
                continue
            # Verify attribute(s) match
            if not self.match_attributes(el, selector.attributes):
                continue
            # Verify pseudo selector patterns
            if selector.selectors and not self.match_selectors(el, selector.selectors):
                continue
            # Verify relationship selectors
            if selector.relation and not self.match_relations(el, selector.relation):
                continue
            match = not selector.is_not
            break

        return match

    def match(self, el):
        """Match."""

        return self.match_selectors(el, self.selectors)
