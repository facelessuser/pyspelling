"""Test utilities."""
import contextlib
import os
import shutil
import unittest
import warnings
from textwrap import dedent
from pyspelling import spellcheck
import sys

# Below is general helper stuff that Python uses in `unittests`.  As these
# not meant for users, and could change without notice, include them
# ourselves so we aren't surprised later.
TESTFN = '@test'
WIN = sys.platform.startswith('win')
HUNSPELL = 'hunspell.exe' if WIN else 'hunspell'
ASPELL = 'aspell.exe' if WIN else 'aspell'

# Disambiguate `TESTFN` for parallel testing, while letting it remain a valid
# module name.
TESTFN = "{}_{}_tmp".format(TESTFN, os.getpid())


def which(executable):
    """See if executable exists."""

    location = None
    if os.path.basename(executable) != executable:
        if os.path.isfile(executable):
            location = executable
    else:
        paths = [x for x in os.environ["PATH"].split(os.pathsep) if not x.isspace()]
        paths.extend([x for x in os.environ.get("TOX_SPELL_PATH", "").split(os.pathsep) if not x.isspace()])
        for path in paths:
            exe = os.path.join(path, executable)
            if os.path.isfile(exe):
                location = exe
                break
    return location


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

    def setup_fs(self):
        """Setup file system (common files used across multiple tests)."""

    def tearDown(self):
        """Cleanup."""

        retry = 3
        while retry:
            try:
                shutil.rmtree(self.tempdir)
                retry = 0
            except Exception:
                retry -= 1

    def assert_spell_required(self, running):
        """Check if what we are running matches what we request."""

        required = os.environ.get("TOX_SPELL_REQUIRE", "any")

        if required not in ("both", "any", "aspell", "hunspell"):
            raise RuntimeError("Invalid value of '{}' in 'TOX_SPELL_REQUIRE'".format(required))

        if running not in ("both", "aspell", "hunspell"):
            raise RuntimeError(
                "Required tests are not being run (currently running '{}'). ".format(running) +
                "Make sure spell checker can be found and " +
                "'TOX_SPELL_REQUIRE' is set appropriately (currently '{}')".format(required)
            )

        if required != running and (required != "any" and running != "both"):
            raise RuntimeError(
                "'TOX_SPELL_REQUIRE' env variable, which is "
                "'{}', is not compatible with '{}'".format(running, required)
            )

    def assert_spellcheck(self, config_file, expected, names=None, groups=None, sources=None, verbose=4):
        """Spell check."""

        hunspell_location = which(HUNSPELL)
        aspell_location = which(ASPELL)
        if hunspell_location and aspell_location:
            running = "both"
        elif hunspell_location:
            running = "hunspell"
        elif aspell_location:
            running = "aspell"
        else:
            running = "none"
        self.assert_spell_required(running)

        if hunspell_location:
            words = set()
            for results in spellcheck(
                os.path.join(self.tempdir, config_file),
                names=names,
                groups=groups,
                sources=sources,
                checker='hunspell',
                binary=hunspell_location,
                debug=True,
                verbose=verbose
            ):
                if results.error:
                    print(results.error)
                words |= set(results.words)
            self.assertEqual(sorted(expected), sorted(list(words)))
        if aspell_location:
            words = set()
            for results in spellcheck(
                os.path.join(self.tempdir, config_file),
                names=names,
                groups=groups,
                sources=sources,
                checker='aspell',
                binary=aspell_location,
                debug=True,
                verbose=verbose
            ):
                if results.error:
                    print(results.error)
                words |= set(results.words)
            self.assertEqual(sorted(expected), sorted(list(words)))
