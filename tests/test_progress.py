"""Test progress reporting."""
import io
import os
import unittest
from unittest import mock
from pyspelling import spellcheck
from pyspelling.__main__ import Progress
from . import util


class FakeStream(io.StringIO):
    """String stream that can pretend to be a terminal."""

    def __init__(self, tty):
        """Initialize."""

        super().__init__()
        self.tty = tty

    def isatty(self):
        """Report whether this is a terminal."""

        return self.tty


class TestProgressRenderer(unittest.TestCase):
    """Test the command line progress renderer."""

    def test_non_tty_throttled(self):
        """Test that non-terminal output prints a line every 10% and a summary."""

        stream = FakeStream(False)
        progress = Progress(stream)
        progress('task', 0, 20, None, False)
        for i in range(1, 21):
            progress('task', i, 20, f'file{i}.txt', i == 5)

        lines = stream.getvalue().splitlines()
        self.assertNotIn('\r', stream.getvalue())
        self.assertEqual(lines[:-1], [f'[task] {i}/20 files' for i in range(2, 20, 2)])
        self.assertRegex(lines[-1], r'^\[task\] 20 files checked, 1 with errors \(\d+\.\ds\)$')

    def test_tty_redraws_line(self):
        """Test that terminal output redraws a single line and ends with a summary."""

        stream = FakeStream(True)
        progress = Progress(stream)
        progress('task', 0, 2, None, False)
        progress('task', 1, 2, 'a.txt', False)
        self.assertTrue(stream.getvalue().endswith('\r\033[K[task] 1/2 files (50%) a.txt'))

        progress('task', 2, 2, 'b.txt', True)
        self.assertRegex(
            stream.getvalue(),
            r'\r\033\[K\[task\] 2 files checked, 1 with errors \(\d+\.\ds\)\n$'
        )

    def test_tty_clear_and_redraw(self):
        """Test that the status line can be cleared and restored around other output."""

        stream = FakeStream(True)
        progress = Progress(stream)
        progress('task', 0, 3, None, False)
        progress('task', 1, 3, 'a.txt', False)
        stream.seek(0)
        stream.truncate()

        progress.clear()
        self.assertEqual(stream.getvalue(), '\r\033[K')
        progress.redraw()
        self.assertEqual(stream.getvalue(), '\r\033[K\r\033[K[task] 1/3 files (33%) a.txt')

    def test_tty_clear_after_summary(self):
        """Test that nothing is erased once the summary has been written."""

        stream = FakeStream(True)
        progress = Progress(stream)
        progress('task', 0, 1, None, False)
        progress('task', 1, 1, 'a.txt', False)
        value = stream.getvalue()
        progress.clear()
        progress.redraw()
        self.assertEqual(stream.getvalue(), value)

    def test_tty_truncates_file_name(self):
        """Test that long file names are shortened from the left to fit the terminal."""

        stream = FakeStream(True)
        progress = Progress(stream)
        progress('task', 0, 2, None, False)
        with mock.patch('shutil.get_terminal_size', return_value=os.terminal_size((40, 24))):
            progress('task', 1, 2, 'some/very/long/path/to/a/file.txt', False)

        line = stream.getvalue().rsplit('\r\033[K', 1)[-1]
        self.assertEqual(len(line), 39)
        self.assertTrue(line.startswith('[task] 1/2 files (50%) ...'))
        self.assertTrue(line.endswith('file.txt'))

    def test_no_files(self):
        """Test that a task without files still prints a summary."""

        for tty in (True, False):
            stream = FakeStream(tty)
            Progress(stream)('task', 0, 0, None, False)
            self.assertRegex(stream.getvalue(), r'^\[task\] 0 files checked, 0 with errors \(\d+\.\ds\)\n$')


class TestProgressCallback(util.PluginTestCase):
    """Test the progress callback of `spellcheck`."""

    def setup_fs(self):
        """Setup files."""

        config = self.dedent(
            """
            matrix:
            - name: progress
              default_encoding: utf-8
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
                d: en_US
              hunspell:
                d: en_US
              pipeline: null
            """
        ).format(self.tempdir)
        self.mktemp('.progress.yml', config, 'utf-8')
        self.mktemp('good.txt', 'yes word', 'utf-8')
        self.mktemp('bad.txt', 'helo begn', 'utf-8')

    def get_checker(self):
        """Get an available spell checker."""

        hunspell_location = util.which(util.HUNSPELL)
        aspell_location = util.which(util.ASPELL)
        if hunspell_location and aspell_location:
            running = "both"
        elif hunspell_location:
            running = "hunspell"
        elif aspell_location:
            running = "aspell"
        else:
            running = "none"
        self.assert_spell_required(running)
        if aspell_location:
            return 'aspell', aspell_location
        return 'hunspell', hunspell_location

    def collect(self, jobs):
        """Run the spell check and collect progress events and results."""

        checker, binary = self.get_checker()
        events = []
        results = []

        def callback(*args):
            events.append(args)

        for result in spellcheck(
            os.path.join(self.tempdir, '.progress.yml'),
            checker=checker,
            binary=binary,
            jobs=jobs,
            progress=callback
        ):
            # Each file must be reported before its results are yielded.
            self.assertEqual(events[-1][3], result.context)
            results.append(result)
        return events, results

    def assert_events(self, events):
        """Check the reported progress events."""

        self.assertEqual(events[0], ('progress', 0, 2, None, False))
        self.assertEqual([e[1:3] for e in events[1:]], [(1, 2), (2, 2)])
        failed = {os.path.basename(e[3]): e[4] for e in events[1:]}
        self.assertEqual(failed, {'good.txt': False, 'bad.txt': True})

    def test_progress_single(self):
        """Test progress events without multi-processing."""

        events, results = self.collect(1)
        self.assert_events(events)
        self.assertEqual(sorted(w for r in results for w in r.words), ['begn', 'helo'])

    def test_progress_parallel(self):
        """Test progress events with multi-processing."""

        events, results = self.collect(2)
        self.assert_events(events)
        self.assertEqual(sorted(w for r in results for w in r.words), ['begn', 'helo'])
