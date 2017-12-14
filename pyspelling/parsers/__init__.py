"""Plugins."""
from __future__ import unicode_literals
import re
import codecs
import contextlib
import mmap
import os
import functools
from collections import namedtuple

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


class SourceText(namedtuple('SourceText', ['text', 'context', 'encoding', 'type'])):
    """Ignore rule."""


class Decoder(object):
    """
    Simple detect encoding class.

    Attempts to detect UTF encoding via BOMs.
    Override `special_encode_check` to add additional check logic.
    """

    MAX_GUESS_SIZE = 31457280

    def _is_very_large(self, size):
        """Check if content is very large."""

        return size >= self.MAX_GUESS_SIZE

    def _verify_encode(self, file_obj, encoding, blocks=1, chunk_size=4096):
        """
        Iterate through the file chunking the data into blocks and decoding them.

        Here we can adjust how the size of blocks and how many to validate. By default,
        we are just going to check the first 4K block.
        """

        good = True
        file_obj.seek(0)
        binary_chunks = iter(functools.partial(file_obj.read, chunk_size), b"")
        try:
            for unicode_chunk in codecs.iterdecode(binary_chunks, encoding):  # noqa
                if blocks:
                    blocks -= 1
                else:
                    break
        except Exception:
            good = False
        return good

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

    def utf_strip_bom(self, encoding):
        """Return an encoding that will ignore the BOM."""

        if encoding is None:
            pass
        elif encoding == 'utf-8':
            encoding = 'utf-8-sig'
        elif encoding.startswith('utf-16'):
            encoding = 'utf-16'
        elif encoding.startswith('utf-32'):
            encoding = 'utf-32'
        return encoding

    def special_encode_check(self, content, ext):
        """Special encode check."""

        return None

    def _detect_encoding(self, f, ext, file_size):
        """Guess by checking BOM, and checking `_special_encode_check`, and using memory map."""

        encoding = None
        with contextlib.closing(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)) as m:
            # Check for boms
            encoding = self._has_bom(m.read(4))
            m.seek(0)
            # Check file extensions
            if encoding is None:
                encoding = self.utf_strip_bom(self.special_encode_check(m.read(1024), ext))

        return encoding

    def guess(self, filename, verify=True, verify_blocks=1, verify_block_size=4096):
        """Guess the encoding and decode the content of the file."""

        encoding = None

        try:
            ext = os.path.splitext(filename)[1].lower()
            file_size = os.path.getsize(filename)
            # If the file is really big, lets just call it binary.
            # We dont' have time to let Python chug through a massive file.
            if not self._is_very_large(file_size):
                with open(filename, "rb") as f:
                    if file_size == 0:
                        encoding = 'ascii'
                    else:
                        encoding = self._detect_encoding(f, ext, file_size)

                    if verify and encoding and encoding != 'bin':
                        if not self.verify_encode(f, encoding.encode, verify_blocks, verify_block_size):
                            encoding = 'bin'
            else:
                encoding = 'bin'
        except Exception:  # pragma: no cover
            encoding = 'bin'
            pass

        return encoding


class Parser(object):
    """Spelling language."""

    EXTENSIONS = tuple('*',)
    DECODER = Decoder

    def __init__(self, config, encoding='ascii'):
        """Initialize."""

        self.default_encoding = encoding

    def detect_encoding(self, source_file):
        """Detect encoding."""

        detect = self.DECODER()
        encoding = detect.guess(source_file, verify=False)
        # If we didn't explicitly detect an encoding, assume default.
        if not encoding:
            encoding = self.default_encoding

        return self.default_encoding if not encoding else encoding

    def parse_file(self, source_file):
        """Parse HTML file."""

        encoding = self.detect_encoding(source_file)

        if encoding != 'bin':
            with codecs.open(source_file, 'r', encoding=encoding) as f:
                text = f.read()
        else:
            text = ''
        return [SourceText(text, source_file, encoding, 'text')]
