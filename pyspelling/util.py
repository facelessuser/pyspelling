"""Utilities."""
from __future__ import unicode_literals
import subprocess
import sys
import string
import random
from collections import namedtuple

PY3 = sys.version_info >= (3, 0)

if PY3:
    string_type = str
    ustr = str
    bstr = bytes
else:
    string_type = basestring  # noqa
    ustr = unicode  # noqa
    bstr = str


def console(cmd, input_file=None, input_text=None):
    """Call with arguments."""

    returncode = None
    output = None

    if sys.platform.startswith('win'):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        process = subprocess.Popen(
            cmd,
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            shell=False
        )
    else:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            shell=False
        )

    if input_file is not None:
        with open(input_file, 'rb') as f:
            process.stdin.write(f.read())
    if input_text is not None:
        process.stdin.write(input_text)
    output = process.communicate()
    returncode = process.returncode

    assert returncode == 0, "Runtime Error: %s" % (
        output[0].rstrip().decode('utf-8') if PY3 else output[0]
    )

    return output[0].decode('utf-8') if PY3 else output[0]


def random_name_gen(size=6):
    """Generate a random python attribute name."""

    return ''.join(
        [random.choice(string.ascii_uppercase)] +
        [random.choice(string.ascii_uppercase + string.digits) for i in range(size - 1)]
    ) if size > 0 else ''


class SourceText(namedtuple('SourceText', ['text', 'context', 'encoding', 'category', 'error'])):
    """Source text."""

    __slots__ = ()

    def __new__(cls, text, context, encoding, category, error=None):
        """Allow defaults."""

        return super(SourceText, cls).__new__(cls, text, context, encoding, category, error)

    def _is_bytes(self):
        """Is bytes."""

        return isinstance(self.text, bstr)

    def _has_error(self):
        """Check if object has an error associated with it."""

        return self.error is not None
