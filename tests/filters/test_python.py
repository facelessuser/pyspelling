"""Test Python plugin."""
from .. import util


class TestPython(util.PluginTestCase):
    """Test Python plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: python
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              pipeline:
              - pyspelling.filters.python:
                  group_comments: true
            """
        ).format(self.tempdir)
        self.mktemp('.python.yml', config, 'utf-8')

    def test_python(self):
        """Test Python."""

        bad_docstring = ['helo', 'begn']
        bad_comments = ['flga', 'graet']
        bad_comments2 = ['recieve', 'teh']
        bad_words = bad_docstring + bad_comments + bad_comments2
        good_words = ['yes', 'word']
        template = self.dedent(
            """
            \"""
            {}
            \"""
            def function():
                # {}
                # {}
            """
        ).format(
            '\n'.join(bad_docstring + good_words),
            ' '.join(bad_comments + good_words),
            ' '.join(bad_comments2 + good_words)
        )
        self.mktemp('test.txt', template, 'utf-8')
        words = self.spellcheck('.python.yml')
        self.assertEqual(sorted(bad_words), words)


class TestPythonChained(util.PluginTestCase):
    """Test Python plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: python
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              pipeline:
              - pyspelling.filters.text:
              - pyspelling.filters.python:
                  group_comments: true
            """
        ).format(self.tempdir)
        self.mktemp('.python.yml', config, 'utf-8')

    def test_python_after_text(self):
        """Test Python after text."""

        bad_docstring = ['helo', 'begn']
        bad_comments = ['flga', 'graet']
        bad_comments2 = ['recieve', 'teh']
        bad_words = bad_docstring + bad_comments + bad_comments2
        good_words = ['yes', 'word']
        template = self.dedent(
            """
            \"""
            {}
            \"""
            def function():
                # {}
                # {}
            """
        ).format(
            '\n'.join(bad_docstring + good_words),
            ' '.join(bad_comments + good_words),
            ' '.join(bad_comments2 + good_words)
        )
        self.mktemp('test.txt', template, 'utf-8')
        words = self.spellcheck('.python.yml')
        self.assertEqual(sorted(bad_words), words)
