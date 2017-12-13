"""Markdown filter."""
from __future__ import unicode_literals
from .. import filters
import markdown
from .. import util


class MarkdownFilter(filters.Filter):
    """Markdown filter."""

    def __init__(self, options):
        """Initialize."""

        extensions = []
        extension_configs = {}
        for item in options.get('markdown_extensions', []):
            if isinstance(item, util.ustr):
                extensions.append(item)
            else:
                k, v = list(item.items())[0]
                extensions.append(k)
                if v is not None:
                    extension_configs[k] = v
        self.markdown = markdown.Markdown(extensions=extensions, extension_configs=extension_configs)

    def filter(self, text):
        """Apply Markdown filter."""

        self.markdown.reset()
        return self.markdown.convert(text)
