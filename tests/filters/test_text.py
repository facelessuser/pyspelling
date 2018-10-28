"""Test text plugin."""
from .. import util


class TestText(util.PluginTestCase):
    """Test text plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: text
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              pipeline:
              - pyspelling.filters.text:
                  convert_encoding: utf-8
            """.format(self.tempdir)
        )
        self.mktemp('.text.yml', config, 'utf-8')

    def test_text(self):
        """Test text."""

        bad_words = ['helo', 'begn']
        self.mktemp('test.txt', '\n'.join(bad_words), 'utf-8')
        words = self.spellcheck('.text.yml')
        self.assertEqual(sorted(bad_words), words)

    def test_text_utf16(self):
        """Test text."""

        bad_words = ['helo', 'begn']
        self.mktemp('test.txt', '\n'.join(bad_words), 'utf-16')
        words = self.spellcheck('.text.yml')
        self.assertEqual(sorted(bad_words), words)

    def test_text_utf32(self):
        """Test text."""

        bad_words = ['helo', 'begn']
        self.mktemp('test.txt', '\n'.join(bad_words), 'utf-32')
        words = self.spellcheck('.text.yml')
        self.assertEqual(sorted(bad_words), words)


class TestTextChained(util.PluginTestCase):
    """Test text extension."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: text
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              pipeline:
              - pyspelling.filters.python:
              - pyspelling.filters.text:
                  convert_encoding: utf-8
            """.format(self.tempdir)
        )
        self.mktemp('.text.yml', config, 'utf-8')

    def test_text_after_python(self):
        """Test text."""

        bad_words = ['helo', 'begn']
        template = self.dedent(
            """
            \"""
            {}
            \"""
            """.format('\n'.join(bad_words))
        )
        self.mktemp('test.txt', template, 'utf-8')
        words = self.spellcheck('.text.yml')
        self.assertEqual(sorted(bad_words), words)
