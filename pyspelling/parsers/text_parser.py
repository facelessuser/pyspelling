"""Text parser."""
from __future__ import unicode_literals
from .. import parsers


class TextParser(parsers.Parser):
    """Text parser."""

    EXTENSIONS = ('*.txt', '*.text')


def get_parser():
    """Return the parser."""

    return TextParser
