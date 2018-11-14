"""Stylesheets filter."""
import re
from . import cpp

RE_CSS_COMMENT = re.compile(
    r'''(?x)
        (?P<comments>
            (?P<block>/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)                        # multi-line comments
        ) |
        (?P<code>
            "(?:\\.|[^"\\])*" |                                              # double quotes
            '(?:\\.|[^'\\])*' |                                              # single quotes
            .[^/"']*?                                                        # everything else
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

        super().__init__(options, default_encoding)

    def get_default_config(self):
        """Get default configuration."""

        return {
            "block_comments": True,
            "line_comments": True,
            "group_comments": False,
            "stylesheets": 'css'
        }

    def validate_options(self, k, v):
        """Validate options."""

        super().validate_options(k, v)
        if k == 'stylesheets' and v not in STYLESHEET_TYPE:
            raise ValueError("{}: '{}' is not a valid value for '{}'".format(self.__class__.__name, v, k))

    def setup(self):
        """Setup."""

        self.blocks = self.config['block_comments']
        self.lines = self.config['line_comments']
        self.group_comments = self.config['group_comments']
        # If the style isn't found, just go with CSS, then use the appropriate prefix.
        self.stylesheets = STYLESHEET_TYPE.get(self.config['stylesheets'].lower(), CSS)
        self.prefix = [k for k, v in STYLESHEET_TYPE.items() if v == SASS][0]
        if self.stylesheets == CSS:
            self.pattern = RE_CSS_COMMENT

    def evaluate(self, m):
        """Search for comments."""

        if self.stylesheets == CSS:
            g = m.groupdict()
            if g["code"]:
                self.line_num += g["code"].count('\n')
            else:
                self.evaluate_block(g)
                self.line_num += g['comments'].count('\n')
        else:
            super().evaluate(m)

    def extend_src(self, content, context, encoding):
        """Extend source list."""

        self.extend_src_text(content, context, self.block_comments, encoding, 'block-comment')
        if self.stylesheets != CSS:
            self.extend_src_text(content, context, self.line_comments, encoding, 'line-comment')


def get_plugin():
    """Get filter."""

    return StylesheetsFilter
