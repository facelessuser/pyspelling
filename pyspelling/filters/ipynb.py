"""Jupyter Notebook Filter."""
from .. import filters
import codecs
import json

class IpynbFilter(filters.Filter):
    """Jupyter Notebook Filter."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super().__init__(options, default_encoding)

    def get_default_config(self):
        """Get default configuration."""

        return {}

    def setup(self):
        """Setup."""
        # nothing to do here

    def filter(self, source_file, encoding):
        """Parse Jupyter Notebook."""
        with codecs.open(source_file, 'r', encoding=encoding) as f:
            text = f.read()
            return self.sfilter(text, source_file=source_file, encoding=encoding)

    def sfilter(self, source, source_file="", encoding=""):
        """Filter."""
        if source_file == "":
            source_file = source.context
        if encoding == "":
            encoding = source.encoding
        notebook_data = json.loads(source)
        markdown_sections = []
        for cell in notebook_data["cells"]:
            if cell["cell_type"] == "markdown":
                cell_string = ""
                for markdown_line in cell["source"]:
                    cell_string += markdown_line
                markdown_sections.append(filters.SourceText(cell_string, source_file, encoding, 'ipynb'))
        
        return markdown_sections

def get_plugin():
    """Return the filter."""

    return IpynbFilter
