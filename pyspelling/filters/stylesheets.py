"""Stylesheets filter."""
import re
from . import cpp

RE_CSS_COMMENT = re.compile(
    r'''(?x)
        (?P<comments>
            (?P<block>/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)                        # multi-line comments
        )
      | (?P<code>
            "(?:\\.|[^"\\])*"                                                # double quotes
            '(?:\\.|[^'\\])*'                                                # single quotes
          | .[^/"']*?                                                        # everything else
        )
    ''',
    re.DOTALL | re.MULTILINE
)

CSS = 0
SASS = 1
SCSS = 2

STYLESHEET_TYPE = {
    "css": CSS,
    "sass": SASS,
    "scss": SCSS
}


class StylesheetsFilter(cpp.CppFilter):
    """Stylesheets filter."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        # If the style isn't found, just go with CSS, then use the appropriate prefix.
        self.stylesheets = STYLESHEET_TYPE.get(options.get('stylesheets', 'css').lower(), CSS)
        self.prefix = [k for k, v in STYLESHEET_TYPE.items() if v == SASS][0]
        super(StylesheetsFilter, self).__init__(options, default_encoding)

    def find_comments(self, text):
        """Find comments."""

        if self.stylesheets == CSS:
            for m in RE_CSS_COMMENT.finditer(text):
                self._css_evaluate(m)
        else:
            super(StylesheetsFilter, self).find_comments(text)

    def _css_evaluate(self, m):
        """Search for comments."""

        g = m.groupdict()
        if g["code"]:
            self.line_num += g["code"].count('\n')
        else:
            self.evaluate_block(g)
            self.line_num += g['comments'].count('\n')

    def extend_src(self, content, context, encoding):
        """Extend source list."""

        self.extend_src_text(content, context, self.block_comments, encoding, 'block-comment')
        if self.stylesheets != CSS:
            self.extend_src_text(content, context, self.line_comments, encoding, 'line-comment')


def get_plugin():
    """Get filter."""

    return StylesheetsFilter
