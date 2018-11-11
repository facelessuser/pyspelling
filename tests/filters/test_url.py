"""Test URL plugin."""
from .. import util


class TestURL(util.PluginTestCase):
    """Test URL plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: url
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
                mode: none
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.url:
            """
        ).format(self.tempdir)
        self.mktemp('.url.yml', config, 'utf-8')

    def test_url(self):
        """Test URL."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        text = self.dedent(
            """
            Here is a bad link https://lskjas.com.
            {}
            Here is a bad email slakj.dlaks@mail.com.
            """
        ).format(' '.join(bad_words + good_words))
        self.mktemp('test.txt', text, 'utf-8')
        self.assert_spellcheck('.url.yml', bad_words)


class TestURLChained(util.PluginTestCase):
    """Test chained URL plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: url
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
                mode: none
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.text:
              - pyspelling.filters.url:
            """
        ).format(self.tempdir)
        self.mktemp('.url.yml', config, 'utf-8')

    def test_url_after_text(self):
        """Test URL."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        text = self.dedent(
            """
            Here is a bad link https://lskjas.com.
            {}
            Here is a bad email slakj.dlaks@mail.com.
            """
        ).format(' '.join(bad_words + good_words))
        self.mktemp('test.txt', text, 'utf-8')
        self.assert_spellcheck('.url.yml', bad_words)
