"""Test command line runner."""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from pyspelling.__main__ import run


class TestRun(unittest.TestCase):
    """Test `run`."""

    def test_unknown_name_reports_clean_error(self):
        """Test that an unknown task name fails cleanly instead of a traceback."""

        with tempfile.TemporaryDirectory() as tempdir:
            config = os.path.join(tempdir, 'spelling.yml')
            with open(config, 'w', encoding='utf-8') as f:
                f.write('matrix:\n- name: docs\n  sources:\n  - "*.md"\n')
            out = io.StringIO()
            err = io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                failed = run(config, names=['does-not-exist'])
            self.assertTrue(failed)
            self.assertIn('ERROR', out.getvalue())
            self.assertNotIn('Traceback', err.getvalue())
