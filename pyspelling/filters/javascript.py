"""JavaScript filter."""
import re
from . import cpp

RE_JSDOC = re.compile(r"(?s)^/\*\*$(.*?)[ \t]*\*/", re.MULTILINE)


class JavaScriptFilter(cpp.CppFilter):
    """JavaScript filter."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        self.jsdocs = options.get('jsdocs', False) is True
        options['prefix'] = 'js'
        super(JavaScriptFilter, self).__init__(options, default_encoding)

    def evaluate_block(self, groups):
        """Evaluate block comments."""

        if self.jsdocs:
            m1 = RE_JSDOC.match(groups['comments'])
            if m1:
                lines = []
                for line in m1.group(1).splitlines(True):
                    l = line.lstrip()
                    lines.append(l[1:] if l.startswith('*') else l)
                self.jsdoc_comments.append([''.join(lines), self.line_num])
            elif self.blocks:
                self.block_comments.append([groups['block'][2:-2], self.line_num])
        elif self.blocks:
            self.block_comments.append([groups['block'][2:-2], self.line_num])

    def extend_src(self, content, context, encoding):
        """Extend source list."""

        self.extend_src_text(content, context, self.block_comments, encoding, 'block-comment')
        self.extend_src_text(content, context, self.line_comments, encoding, 'line-comment')
        self.extend_src_text(content, context, self.jsdoc_comments, encoding, 'docs')

    def _filter(self, text, context, encoding):
        """Filter JavaScript comments."""

        self.jsdoc_comments = []
        return super(JavaScriptFilter, self)._filter(text, context, encoding)


def get_plugin():
    """Get filter."""

    return JavaScriptFilter
