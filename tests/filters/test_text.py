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
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.text:
                  convert_encoding: utf-8
            """
        ).format(self.tempdir)
        self.mktemp('.text.yml', config, 'utf-8')

    def test_text(self):
        """Test text."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        self.mktemp('test.txt', '\n'.join(bad_words + good_words), 'utf-8')
        self.assert_spellcheck('.text.yml', bad_words)

    def test_text_utf16(self):
        """Test text `UTF-16`."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        self.mktemp('test.txt', '\n'.join(bad_words + good_words), 'utf-16')
        self.assert_spellcheck('.text.yml', bad_words)

    def test_text_utf32(self):
        """Test text `UTF-32`."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        self.mktemp('test.txt', '\n'.join(bad_words + good_words), 'utf-32')
        self.assert_spellcheck('.text.yml', bad_words)


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
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.python:
              - pyspelling.filters.text:
                  convert_encoding: utf-8
            """
        ).format(self.tempdir)
        self.mktemp('.text.yml', config, 'utf-8')

    def test_text_after_python(self):
        """Test text after Python."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        template = self.dedent(
            """
            \"""
            {}
            \"""
            """
        ).format('\n'.join(bad_words + good_words))
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.text.yml', bad_words)
