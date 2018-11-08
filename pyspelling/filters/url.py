"""URL filter."""
from __future__ import unicode_literals
from .. import filters
import codecs
import re

# Bare link/email detection
RE_MAIL = re.compile(
    r'''(?xi)
    (?P<mail>
        (?<![-/\+@a-z\d_])(?:[-+a-z\d_]([-a-z\d_+]|\.(?!\.))*)  # Local part
        (?<!\.)@(?:[-a-z\d_]+\.)                                # @domain part start
        (?:(?:[-a-z\d_]|(?<!\.)\.(?!\.))*)[a-z]\b               # @domain.end (allow multiple dot names)
        (?![-@])                                                # Don't allow last char to be followed by these
    )
    '''
)

RE_LINK = re.compile(
    r'''(?xi)
    (?P<link>
        (?:(?<=\b)|(?<=_))(?:
            (?:ht|f)tps?://(?:(?:[^_\W][-\w]*(?:\.[-\w.]+)+)|localhost)|  # (http|ftp)://
            (?P<www>w{3}\.)[^_\W][-\w]*(?:\.[-\w.]+)+                     # www.
        )
        /?[-\w.?,!'(){}\[\]/+&@%$#=:"|~;]*                                # url path, fragments, and query stuff
        (?:[^_\W]|[-/#@$+=])                                              # allowed end chars
    )
    '''
)


class URLFilter(filters.Filter):
    """URL filter."""

    def __init__(self, options, default_encoding='utf-8'):
        """Initialization."""

        super().__init__(options, default_encoding)

    def get_default_config(self):
        """Get default configuration."""

        return {
            "emails": True,
            "urls": True
        }

    def setup(self):
        """Setup."""

        self.emails = self.config['emails']
        self.urls = self.config['urls']

    def _filter(self, text):
        """Filter out the URL and email addresses."""

        if self.urls:
            text = RE_LINK.sub('', text)
        if self.emails:
            text = RE_MAIL.sub('', text)
        return text

    def filter(self, source_file, encoding):  # noqa A001
        """Open and filter the file from disk."""

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            text = f.read()

        return [filters.SourceText(self._filter(text), source_file, encoding, 'url-free')]

    def sfilter(self, source):
        """Execute filter."""

        return [filters.SourceText(self._filter(source.text), source.context, source.encoding, 'url-free')]


def get_plugin():
    """Return the filter."""

    return URLFilter
