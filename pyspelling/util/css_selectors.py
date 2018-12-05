"""CSS selector matcher."""
import re
from collections import namedtuple
import bs4

DOC = bs4.BeautifulSoup
TAG = bs4.element.Tag
HAS_CHILD = (TAG, bs4.Doctype, bs4.Declaration, bs4.CData, bs4.ProcessingInstruction)

# Selector patterns
CSS_ESCAPES = r'(?:\\[a-fA-F0-9]{1,6}[ ]?|\\.)'
NTH = r'(?:[-+])?(?:\d+n?|n)(?:(?<=n)\s*(?:[-+])\s*(?:\d+))?'
HTML_SELECTORS = r"""
(?P<class_id>(?:\#|\.)(?:[-\w]|{esc})+) |                            #.class and #id
(?P<ns_tag>(?:(?:(?:[-\w]|{esc})+|\*)?\|)?(?:(?:[-\w]|{esc})+|\*)) | # namespace:tag
\[(?P<ns_attr>(?:(?:(?:[-\w]|{esc})+|\*)?\|)?(?:[-\w]|{esc})+)
""".format(esc=CSS_ESCAPES)
XML_SELECTORS = r"""
(?P<ns_tag>(?:(?:(?:[-\w.]|{esc})+|\*)?\|)?(?:(?:[-\w.]|{esc})+|\*)) | # namespace:tag
\[(?P<ns_attr>(?:(?:(?:[-\w]|{esc})+|\*)\|)?(?:[-\w.]|{esc})+)         # namespace:attributes
""".format(esc=CSS_ESCAPES)
SELECTORS = r'''(?x)
    (?P<pseudo_open>:(?:has|is|matches|not|where)\() |                            # optinal pseudo selector wrapper
    (?P<pseudo>:(?:empty|root|(?:first|last|only)-(?:child|of-type))) |           # Simple pseudo selector
    (?P<pseudo_nth_child>:nth-(?:last-)?child
        \(\s*(?P<nth_child>{nth}|even|odd)\s*(?:\)|(?<=\s)of\s+)) |               # Pseudo `nth-child` selectors
    (?P<pseudo_nth_type>:nth-(?:last-)?of-type
        \(\s*(?P<nth_type>{nth}|even|odd)\s*\)) |                                 # Pseudo `nth-of-type` selectors
    {doc_specific}
    (?:(?P<cmp>[~^|*$]?=)                                                         # compare
    (?P<value>"(\\.|[^\\"]+)*?"|'(\\.|[^\\']+)*?'|(?:[^'"\[\] \t\r\n]|{esc})+))?  # attribute value
    (?P<i>[ ]+i)? \] |                                                            # case insensitive
    (?P<pseudo_close>\)) |                                                        # optional pseudo selector close
    (?P<split>\s*?(?P<relation>[,+>~]|[ ](?![,+>~]))\s*) |                        # split multiple selectors
    (?P<invalid>).+                                                               # not proper syntax
'''
RE_HTML_SEL = re.compile(SELECTORS.format(esc=CSS_ESCAPES, nth=NTH, doc_specific=HTML_SELECTORS))
RE_XML_SEL = re.compile(SELECTORS.format(esc=CSS_ESCAPES, nth=NTH, doc_specific=XML_SELECTORS))

# Empty tag pattern (whitespace okay)
RE_NOT_EMPTY = re.compile('[^ \t\r\n]')
# CSS escape pattern
RE_ESC = re.compile(r'(?:(\\[a-fA-F0-9]{1,6}[ ]?)|(\\.))')
# Pattern to break up `nth` specifiers
RE_NTH = re.compile(r'(?P<s1>[-+])?(?P<a>\d+n?|n)(?:(?<=n)\s*(?P<s2>[-+])\s*(?P<b>\d+))?')

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

# Relationships for :has() (forward looking)
REL_HAS_PARENT = ': '
REL_HAS_CLOSE_PARENT = ':>'
REL_HAS_SIBLING = ':~'
REL_HAS_CLOSE_SIBLING = ':+'


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


class Selector:
    """CSS selector."""

    def __init__(self, **kwargs):
        """Initialize."""

        self.tags = kwargs.get('tags', [])
        self.ids = kwargs.get('ids', [])
        self.classes = kwargs.get('classes', [])
        self.attributes = kwargs.get('attributes', [])
        self.nth = kwargs.get('nth', [])
        self.selectors = kwargs.get('selectors', [])
        self.is_not = kwargs.get('is_not', False)
        self.is_empty = kwargs.get('is_empty', False)
        self.relation = kwargs.get('relation', None)
        self.rel_type = kwargs.get('rel_type', None)
        self.is_root = kwargs.get('is_root', False)

    def set_distant_relation(self, value):
        """Set the furthest relation down the chain."""

        if self.relation:
            temp = self.relation
            while temp and temp.relation:
                temp = temp.relation
            temp.relation = value
        else:
            self.relation = value

    def __str__(self):
        """String representation."""

        return (
            'Selector(tags=%r, ids=%r, classes=%r, attributes=%r, selectors=%r, '
            'is_not=%r, relation=%r, rel_type=%r, is_root=%r)'
        ) % (
            self.tags, self.ids, self.classes, self.attributes, self.selectors,
            self.is_not, self.relation, self.rel_type, self.is_root
        )

    __repr__ = __str__


class SelectorTag(namedtuple('SelectorTag', ['name', 'prefix'])):
    """Selector tag."""


class SelectorAttribute(namedtuple('AttrRule', ['attribute', 'prefix', 'pattern'])):
    """Selector attribute rule."""


class SelectorNth(namedtuple('SelectorNth', ['a', 'n', 'b', 'type', 'last', 'selectors'])):
    """Selector nth type."""


class SelectorMatcher:
    """Match tags in Beautiful Soup with CSS selectors."""

    def __init__(self, selector, mode='html', namespaces=None):
        """Initialize."""

        self.mode = mode
        self.re_sel = RE_HTML_SEL if self.mode != 'xml' else RE_XML_SEL
        self.namespaces = namespaces if namespaces else {}
        self.selectors = self.process_selectors(selector)

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

    def parse_attribute_selector(self, sel, m, has_selector):
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
        has_selector = True
        sel.attributes.append(SelectorAttribute(attr, ns, pattern))
        return has_selector

    def parse_tag_pattern(self, sel, m, has_selector):
        """Parse tag pattern from regex match."""

        parts = [unescape(x) for x in m.group('ns_tag').split('|')]
        if len(parts) > 1:
            prefix = parts[0]
            tag = parts[1]
        else:
            tag = parts[0]
            prefix = None
        sel.tags.append(SelectorTag(tag, prefix))
        has_selector = True
        return has_selector

    def parse_pseudo(self, sel, m, has_selector):
        """Parse pseudo."""

        pseudo = m.group('pseudo')[1:]
        if pseudo == 'root':
            sel.is_root = True
            has_selector = True
        elif pseudo == 'empty':
            sel.is_empty = True
        elif pseudo == 'first-child':
            sel.nth.append(SelectorNth(1, False, 0, False, False, []))
        elif pseudo == 'last-child':
            sel.nth.append(SelectorNth(1, False, 0, False, True, []))
        elif pseudo == 'first-of-type':
            sel.nth.append(SelectorNth(1, False, 0, True, False, []))
        elif pseudo == 'last-of-type':
            sel.nth.append(SelectorNth(1, False, 0, True, True, []))
        elif pseudo == 'only-child':
            sel.nth.extend(
                [
                    SelectorNth(1, False, 0, False, False, []),
                    SelectorNth(1, False, 0, False, True, [])
                ]
            )
        elif pseudo == 'only-of-type':
            sel.nth.extend(
                [
                    SelectorNth(1, False, 0, True, False, []),
                    SelectorNth(1, False, 0, True, True, [])
                ]
            )

        return has_selector

    def parse_pseudo_nth(self, sel, m, has_selector, iselector):
        """Parse `nth` pseudo."""

        postfix = '_child' if m.group('pseudo_nth_child') else '_type'
        content = m.group('nth' + postfix)
        if content == 'even':
            s1 = 2
            s2 = 2
            var = True
        elif content == 'odd':
            s1 = 2
            s2 = 1
            var = True
        else:
            nth_parts = RE_NTH.match(content)
            s1 = '-' if nth_parts.group('s1') and nth_parts.group('s1') == '-' else ''
            a = nth_parts.group('a')
            var = a.endswith('n')
            if a.startswith('n'):
                s1 += '1'
            elif var:
                s1 += a[:-1]
            else:
                s1 += a
            s2 = '-' if nth_parts.group('s2') and nth_parts.group('s2') == '-' else ''
            if nth_parts.group('b'):
                s2 += nth_parts.group('b')
            else:
                s2 = '0'
            s1 = int(s1, 16)
            s2 = int(s2, 16)

        if postfix == '_child':
            if m.group('pseudo_nth' + postfix).startswith(':nth-child'):
                sel.nth.append(SelectorNth(s1, var, s2, False, False, []))
            elif m.group('pseudo_nth' + postfix).startswith(':nth-last-child'):
                sel.nth.append(SelectorNth(s1, var, s2, False, True, []))
            if m.group('pseudo_nth' + postfix).strip().endswith('of'):
                # Parse the rest of `of S`.
                temp_sel = iselector
            else:
                # Use default `*|*` for `of S`. Simulate un-closed pseudo.
                temp_sel = self.re_sel.finditer('*|*)')
            sel.nth[-1].selectors.extend(
                self.parse_selectors(
                    temp_sel,
                    True,
                    False,
                    False
                )
            )
        else:
            if m.group('pseudo_nth' + postfix).startswith(':nth-of-type'):
                sel.nth.append(SelectorNth(s1, var, s2, True, False, []))
            elif m.group('pseudo_nth' + postfix).startswith(':nth-last-of-type'):
                sel.nth.append(SelectorNth(s1, var, s2, True, True, []))
        has_selector = True
        return has_selector

    def parse_pseudo_open(self, sel, m, has_selector, iselector, is_pseudo):
        """Parse pseudo with opening bracket."""

        sel.selectors.extend(
            self.parse_selectors(
                iselector,
                True,
                m.group('pseudo_open')[1:-1] == 'not',
                m.group('pseudo_open')[1:-1] == 'has'
            )
        )
        has_selector = True
        return has_selector

    def parse_has_split(self, sel, m, has_selector, selectors, is_pseudo, rel_type):
        """Parse splitting tokens."""

        if m.group('relation') == REL_NONE:
            if not has_selector:
                raise ValueError("Cannot start or end selector with '{}'".format(m.group('relation')))
            sel.rel_type = rel_type
            selectors[-1].set_distant_relation(sel)
            rel_type = REL_HAS_PARENT
            selectors.append(Selector())
        else:
            if has_selector:
                sel.rel_type = rel_type
                selectors[-1].set_distant_relation(sel)
            rel_type = ':' + m.group('relation')
        sel = Selector()

        has_selector = False
        return has_selector, sel, rel_type

    def parse_split(self, sel, m, has_selector, selectors, relations, is_pseudo):
        """Parse splitting tokens."""

        if not has_selector:
            raise ValueError("Cannot start or end selector with '{}'".format(m.group('relation')))
        is_not = sel.is_not
        if m.group('relation') == REL_NONE:
            if not sel.tags and not is_pseudo:
                # Implied `*`
                sel.tags.append(SelectorTag('*', None))
            sel.relation = relations[0] if relations else None
            selectors.append(sel)
            relations.clear()
        else:
            # In this particular case, we are attaching a relation to an element of interest.
            # the `:not()` applies to the element of interest, not the ancestors. `:not()` is really only
            # applied at the sub-selector level `Selector(is_not=False, selector=[Selector(is_not=True)])`
            # We want to see if the element has the proper ancestry, and then apply the `:not()`.
            # In the case of `:not(el1) > el2`, where the ancestor is evaluated with a not, you'd actually get:
            # ```
            # Selector(
            #     tags=['el2'],
            #     relations=[
            #         [
            #             Selector(
            #                 tags=['*'],
            #                 selectors=[
            #                     Selector(
            #                         tags=['el1'],
            #                         is_not=True
            #                     )
            #                 ]
            #             )
            #         ]
            #     ],
            #     rel_type='>'
            # )
            # ```
            sel.relation = relations[0] if relations else None
            sel.rel_type = m.group('relation')
            sel.is_not = False
            relations.clear()
            relations.append(sel)
        sel = Selector(is_not=is_not)

        has_selector = False
        return has_selector, sel

    def parse_classes(self, sel, m, has_selector):
        """Parse classes."""

        selector = m.group('class_id')
        if selector.startswith('.'):
            sel.classes.append(unescape(selector[1:]))
            has_selector = True
        else:
            sel.ids.append(unescape(selector[1:]))
            has_selector = True
        return has_selector

    def parse_selectors(self, iselector, is_pseudo=False, is_not=False, is_has=False):
        """Parse selectors."""

        sel = Selector(is_not=is_not)
        selectors = []
        has_selector = False
        closed = False
        is_html = self.mode != 'xml'
        relations = []
        rel_type = REL_HAS_PARENT
        split_last = False
        if is_has:
            selectors.append(Selector())

        try:
            while True:
                m = next(iselector)

                # Handle parts
                if m.group('pseudo'):
                    has_selector = self.parse_pseudo(sel, m, has_selector)
                elif m.group('pseudo_nth_type') or m.group('pseudo_nth_child'):
                    has_selector = self.parse_pseudo_nth(sel, m, has_selector, iselector)
                elif m.group('pseudo_open'):
                    has_selector = self.parse_pseudo_open(sel, m, has_selector, iselector, is_pseudo)
                elif m.group('pseudo_close'):
                    if split_last:
                        raise ValueError("Cannot end with a combining character")
                    if is_pseudo:
                        closed = True
                        break
                    else:
                        raise ValueError("Bad selector '{}'".format(m.group(0)))
                elif m.group('split'):
                    if split_last:
                        raise ValueError("Cannot have combining character after a combining character")
                    if is_has:
                        has_selector, sel, rel_type = self.parse_has_split(
                            sel, m, has_selector, selectors, is_pseudo, rel_type
                        )
                    else:
                        has_selector, sel = self.parse_split(sel, m, has_selector, selectors, relations, is_pseudo)
                    split_last = True
                    continue
                elif m.group('ns_attr'):
                    has_selector = self.parse_attribute_selector(sel, m, has_selector)
                elif m.group('ns_tag'):
                    if has_selector:
                        raise ValueError("Tag must come first")
                    has_selector = self.parse_tag_pattern(sel, m, has_selector)
                elif is_html and m.group('class_id'):
                    has_selector = self.parse_classes(sel, m, has_selector)
                elif m.group('invalid'):
                    raise ValueError("Bad selector '{}'".format(m.group(0)))
                split_last = False
        except StopIteration:
            pass

        if is_pseudo and not closed:
            raise ValueError("Unclosed `:pseudo()`")

        if split_last:
            raise ValueError("Cannot end with a combining character")

        if has_selector:
            if not sel.tags and not is_pseudo:
                # Implied `*`
                sel.tags.append(SelectorTag('*', None))
            if is_has:
                sel.rel_type = rel_type
                selectors[-1].set_distant_relation(sel)
            else:
                sel.relation = relations[0] if relations else None
                relations.clear()
                selectors.append(sel)
        elif is_has:
            # We will always need to finish a selector when `:has()` is used as it leads with combining.
            raise ValueError('Missing selectors after combining type.')

        return selectors

    def process_selectors(self, selector):
        """
        Process selectors.

        We do our own selectors as BeautifulSoup4 has some annoying quirks,
        and we don't really need to do nth selectors or siblings or
        descendants etc.
        """

        selectors = []
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

    def match_past_relations(self, el, relation):
        """Match past relationship."""

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
            sibling = el.previous_sibling
            while not found and sibling:
                if not isinstance(sibling, TAG):
                    sibling = sibling.previous_sibling
                    continue
                found = self.match_selectors(sibling, [relation])
                sibling = sibling.previous_sibling
        elif relation.rel_type == REL_CLOSE_SIBLING:
            sibling = el.previous_sibling
            while sibling and not isinstance(sibling, TAG):
                sibling = sibling.previous_sibling
            if sibling and isinstance(sibling, TAG):
                found = self.match_selectors(sibling, [relation])
        return found

    def match_future_child(self, parent, relation, recursive=False):
        """Match future child."""

        match = False
        for child in (parent.descendants if recursive else parent.children):
            if not isinstance(child, TAG):
                continue
            match = self.match_selectors(child, [relation])
            if match:
                break
        return match

    def match_future_relations(self, el, relation):
        """Match future relationship."""

        found = False
        if relation.rel_type == REL_HAS_PARENT:
            found = self.match_future_child(el, relation, True)
        elif relation.rel_type == REL_HAS_CLOSE_PARENT:
            found = self.match_future_child(el, relation)
        elif relation.rel_type == REL_HAS_SIBLING:
            sibling = el.next_sibling
            while not found and sibling:
                if not isinstance(sibling, TAG):
                    sibling = sibling.next_sibling
                    continue
                found = self.match_selectors(sibling, [relation])
                sibling = sibling.next_sibling
        elif relation.rel_type == REL_HAS_CLOSE_SIBLING:
            sibling = el.next_sibling
            while sibling and not isinstance(sibling, TAG):
                sibling = sibling.next_sibling
            if sibling and isinstance(sibling, TAG):
                found = self.match_selectors(sibling, [relation])
        return found

    def match_relations(self, el, relation):
        """Match relationship to other elements."""

        found = False

        if relation.rel_type.startswith(':'):
            found = self.match_future_relations(el, relation)
        else:
            found = self.match_past_relations(el, relation)

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

    def match_root(self, el):
        """Match element as root."""

        parent = el.parent
        return parent and not parent.parent

    def match_nth_tag_type(self, el, child):
        """Match tag type for `nth` matches."""

        return(
            (child.name == (lower(el.name) if not self.is_xml() else el.name)) and
            (self.supports_namespaces() and self.get_namespace(child) == self.get_namespace(el))
        )

    def match_nth(self, el, nth):
        """Match `nth` elements."""

        matched = True

        for n in nth:
            matched = False
            if not el.parent:
                break
            if n.selectors and not self.match_selectors(el, n.selectors):
                break
            parent = el.parent
            last = n.last
            last_index = len(parent.contents) - 1
            relative_index = 0
            a = n.a
            b = n.b
            var = n.n
            count = 0
            count_incr = 1
            factor = -1 if last else 1
            index = len(parent.contents) - 1 if last else 0
            idx = last_idx = a * count + b if var else a

            # We can only adjust bounds within a variable index
            if var:
                # Abort if our nth index is out of bounds and only getting further out of bounds as we increment.
                # Otherwise, increment to try to get in bounds.
                while idx < 1 or idx > last_index:
                    diff_low = 0 - idx
                    if idx < 0:
                        count += count_incr
                        idx = last_idx = a * count + b if var else a
                        diff = 0 - idx
                        if diff >= diff_low:
                            break
                        diff_low = diff
                    diff_high = idx - last_index
                    if idx > last_index:
                        count += count_incr
                        idx = last_idx = a * count + b if var else a
                        diff = idx - last_index
                        if diff >= diff_high:
                            break
                        diff_high = diff

                # If a < 0, our count is working backwards, so floor the index by increasing the count.
                # Find the count that yields the lowest, in bound value and use that.
                # Lastly reverse count increment so that we'll increase our index.
                lowest = count
                if a < 0:
                    while idx >= 1:
                        lowest = count
                        count += count_incr
                        idx = last_idx = a * count + b if var else a
                    count_incr = -1
                count = lowest
                idx = last_idx = a * count + b if var else a

            # Evaluate elements while our calculated nth index is still in range
            while 1 <= idx <= last_index:
                child = None
                # Evaluate while our child index is still range.
                while 0 <= index <= last_index:
                    child = parent.contents[index]
                    index += factor
                    if not isinstance(child, TAG):
                        continue
                    # Handle `of S` in `nth-child`
                    if n.selectors and not self.match_selectors(child, n.selectors):
                        continue
                    # Handle `of-type`
                    if n.type and not self.match_nth_tag_type(el, child):
                        continue
                    relative_index += 1
                    if relative_index == idx:
                        if child is el:
                            matched = True
                        else:
                            break
                    if child is el:
                        break
                if child is el:
                    break
                last_idx = idx
                count += count_incr
                if count < 0:
                    # Count is counting down and has now ventured into invalid territory.
                    break
                idx = a * count + b if var else a
                if last_idx == idx:
                    break
            if not matched:
                break
        return matched

    def has_child(self, el):
        """Check if element has child."""

        found_child = False
        for child in el.children:
            if isinstance(child, HAS_CHILD):
                found_child = True
                break
        return found_child

    def match_empty(self, el, is_empty):
        """Check if element is empty (if requested)."""

        return not is_empty or (RE_NOT_EMPTY.search(el.text) is None and not self.has_child(el))

    def match_selectors(self, el, selectors):
        """Check if element matches one of the selectors."""

        match = False
        is_html = self.mode != 'xml'
        for selector in selectors:
            match = selector.is_not
            # Verify tag matches
            if not self.match_tag(el, selector.tags):
                continue
            # Verify `nth` matches
            if not self.match_nth(el, selector.nth):
                continue
            if not self.match_empty(el, selector.is_empty):
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
            if selector.is_root and not self.match_root(el):
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

        return isinstance(el, TAG) and self.match_selectors(el, self.selectors)


def _select(tree, captures, ignores):  # pragma: no cover
    """Recursively return selected tags."""

    if ignores.match(tree):
        if comments:
            for child in tree.descendants:
                if isinstance(child, bs4.Comment):
                    yield child
    else:
        if captures.match(tree):
            yield tree

        # Walk children
        for child in tree.children:
            if isinstance(child, bs4.element.Tag):
                yield from _select(child, captures, ignores, comments)
            elif comments and isinstance(child, bs4.Comment):
                yield child


def comments(tree, mode="html"):  # pragma: no cover
    """Get comments only."""

    select(tree, "", "", mode, None, True)


def select(tree, select, ignore="", mode='html', namespaces=None, comments=False):  # pragma: no cover
    """Select the specified tags filtering out if a filter pattern is provided."""

    captures = SelectorMatcher(select, mode, namespaces)
    ignores = SelectorMatcher(ignore, mode, namespaces)

    yield from _select(tree, captures, ignores, comments)
