"""Test utilities."""
import contextlib
import os
import shutil
import unittest
import warnings
from textwrap import dedent
from pyspelling import spellcheck

# Below is general helper stuff that Python uses in `unittests`.  As these
# not meant for users, and could change without notice, include them
# ourselves so we aren't surprised later.
TESTFN = '@test'

# Disambiguate `TESTFN` for parallel testing, while letting it remain a valid
# module name.
TESTFN = "{}_{}_tmp".format(TESTFN, os.getpid())


@contextlib.contextmanager
def change_cwd(path, quiet=False):
    """
    Return a context manager that changes the current working directory.

    Arguments:
      path: the directory to use as the temporary current working directory.
      quiet: if False (the default), the context manager raises an exception
        on error.  Otherwise, it issues only a warning and keeps the current
        working directory the same.
    """

    saved_dir = os.getcwd()
    try:
        os.chdir(path)
    except OSError:
        if not quiet:
            raise
        warnings.warn('tests may fail, unable to change CWD to: ' + path,
                      RuntimeWarning, stacklevel=3)
    try:
        yield os.getcwd()
    finally:
        os.chdir(saved_dir)


class PluginTestCase(unittest.TestCase):
    """Test plugin."""

    def dedent(self, content):
        """
        Dedent text.

        When dedenting text, you often leave a new line at the start, so strip it as well.
        """

        return dedent(content).replace('\n', '', 1)

    def mktemp(self, filename, content, encoding):
        """Make temp directory."""

        filename = os.path.join(self.tempdir, os.path.normpath(filename))
        base, file = os.path.split(filename)
        if not os.path.exists(base):
            retry = 3
            while retry:
                try:
                    os.makedirs(base)
                    retry = 0
                except Exception:
                    retry -= 1
        with open(filename, "wb") as f:
            f.write(content.encode(encoding))

    def setUp(self):
        """Setup."""

        self.tempdir = TESTFN + "_dir"
        self.setup_fs()

    def tearDown(self):
        """Cleanup."""

        retry = 3
        while retry:
            try:
                shutil.rmtree(self.tempdir)
                retry = 0
            except Exception:
                retry -= 1

    def spellcheck(self, config_file, name=None, binary='', verbose=0, checker='', debug=True):
        """Spell check."""

        words = set()
        for results in spellcheck(os.path.join(self.tempdir, config_file), name, binary, verbose, checker, debug):
            words |= set(results.words)
        return sorted(list(words))
