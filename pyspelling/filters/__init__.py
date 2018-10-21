"""Filter Plugins."""
from __future__ import unicode_literals
import re
import codecs
import contextlib
import mmap
import os
from collections import namedtuple

PYTHON_ENCODING_NAMES = {
    'iso-8859-8-i': 'iso-8859-8',
    'macintosh': 'mac-roman',
    'windows-874': 'cp874',
    'x-mac-cyrillic': 'mac-cyrillic',
    "x-sjis": "shift-jis"
}

RE_UTF_BOM = re.compile(
    b'^(?:(' +
    codecs.BOM_UTF8 +
    b')[\x00-\xFF]{,2}|(' +
    codecs.BOM_UTF32_BE +
    b')|(' +
    codecs.BOM_UTF32_LE +
    b')|(' +
    codecs.BOM_UTF16_BE +
    b')|(' +
    codecs.BOM_UTF16_LE +
    b'))'
)

RE_CATEGORY_NAME = re.compile(r'^[-a-z0-9_]+$', re.I)


class SourceText(namedtuple('SourceText', ['text', 'context', 'encoding', 'category', 'error'])):
    """Source text."""

    __slots__ = ()

    def __new__(cls, text, context, encoding, category, error=None):
        """Allow defaults."""

        encoding = PYTHON_ENCODING_NAMES.get(encoding, encoding).lower()

        if encoding == 'utf-8-sig':
            encoding = 'utf-8'
        if encoding.startswith('utf-16'):
            encoding = 'utf-16'
        elif encoding.startswith('utf-32'):
            encoding = 'utf-32'

        if encoding:
            encoding = codecs.lookup(encoding).name

        if RE_CATEGORY_NAME.match(category) is None and error is None:
            raise ValueError('Invalid category name in SourceText!')

        return super(SourceText, cls).__new__(cls, text, context, encoding, category, error)

    def _is_bytes(self):
        """Is bytes."""

        return isinstance(self.text, bytes)

    def _has_error(self):
        """Check if object has an error associated with it."""

        return self.error is not None


class Filter(object):
    """Spelling language."""

    MAX_GUESS_SIZE = 31457280
    CHECK_BOM = True

    def __init__(self, config, default_encoding='utf-8'):
        """Initialize."""

        self.config = config
        self.default_encoding = PYTHON_ENCODING_NAMES.get(default_encoding, default_encoding).lower()

    def _is_very_large(self, size):
        """Check if content is very large."""

        return size >= self.MAX_GUESS_SIZE

    def _verify_encoding(self, enc):
        """Verify encoding is okay."""

        enc = PYTHON_ENCODING_NAMES.get(enc, enc)
        try:
            codecs.getencoder(enc)
            encoding = enc
        except LookupError:
            encoding = None
        return encoding

    def _has_bom(self, content):
        """Check for UTF8, UTF16, and UTF32 BOMs."""

        encoding = None
        m = RE_UTF_BOM.match(content)
        if m is not None:
            if m.group(1):
                encoding = 'utf-8-sig'
            elif m.group(2):
                encoding = 'utf-32'
            elif m.group(3):
                encoding = 'utf-32'
            elif m.group(4):
                encoding = 'utf-16'
            elif m.group(5):
                encoding = 'utf-16'
        return encoding

    def _utf_strip_bom(self, encoding):
        """Return an encoding that will ignore the BOM."""

        if encoding is None:
            pass
        elif encoding.lower() == 'utf-8':
            encoding = 'utf-8-sig'
        elif encoding.lower().startswith('utf-16'):
            encoding = 'utf-16'
        elif encoding.lower().startswith('utf-32'):
            encoding = 'utf-32'
        return encoding

    def _detect_buffer_encoding(self, f):
        """Guess by checking BOM, and checking `_special_encode_check`, and using memory map."""

        encoding = None
        with contextlib.closing(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)) as m:
            # Check for BOMs
            if self.CHECK_BOM:
                encoding = self._has_bom(m.read(4))
            m.seek(0)
            # Check file extensions
            if encoding is None:
                encoding = self._utf_strip_bom(self.header_check(m.read(1024)))
                m.seek(0)
            if encoding is None:
                m.seek(0)
                encoding = self._utf_strip_bom(self.content_check(m))

        return encoding

    def _detect_encoding(self, source_file):
        """Detect encoding."""

        encoding = self._guess(source_file)
        # If we didn't explicitly detect an encoding, assume default.
        if not encoding:
            encoding = self.default_encoding

        return encoding

    def _parse(self, source_file):
        """Parse the file."""

        self.current_encoding = self.default_encoding
        encoding = None
        try:
            encoding = self._detect_encoding(source_file)
            content = self.filter(source_file, encoding)
        except UnicodeDecodeError as e:
            if not encoding or encoding != self.default_encoding:
                content = self.filter(source_file, self.default_encoding)
            else:
                raise
        return content

    def _guess(self, filename):
        """Guess the encoding and decode the content of the file."""

        encoding = None

        try:
            file_size = os.path.getsize(filename)
            # If the file is really big, lets just call it binary.
            # We don't have time to let Python chug through a massive file.
            if not self._is_very_large(file_size):
                with open(filename, "rb") as f:
                    if file_size == 0:
                        encoding = 'ascii'
                    else:
                        encoding = self._detect_buffer_encoding(f)
                        if encoding is not None:
                            encoding = self._verify_encoding(encoding)
            else:
                raise UnicodeDecodeError('Unicode detection is not applied to very large files!')
        except Exception:  # pragma: no cover
            raise UnicodeDecodeError('Cannot resolve encoding!')
            pass

        return encoding

    def content_check(self, file_handle):
        """File content check."""

        return None

    def header_check(self, content):
        """Special encode check."""

        return None

    def filter(self, source_file, encoding):  # noqa A001
        """Open and filter the file from disk."""

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            text = f.read()
        return [SourceText(text, source_file, encoding, 'text')]

    def sfilter(self, source):
        """Execute filter."""

        return [SourceText(source.text, source.context, source.encoding, 'text')]
