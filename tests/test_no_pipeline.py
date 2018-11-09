"""Test text plugin."""
from . import util


class TestNoPipeline(util.PluginTestCase):
    """Test no pipeline."""

    def test_no_pipeline(self):
        """Test with no pipeline."""

        config = self.dedent(
            """
            matrix:
            - name: no_pipeline
              default_encoding: utf-8
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline: null
            """
        ).format(self.tempdir)
        self.mktemp('.nopipeline.yml', config, 'utf-8')

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        self.mktemp('test.txt', '\n'.join(bad_words + good_words), 'utf-8')
        words = self.spellcheck('.nopipeline.yml')
        self.assertEqual(sorted(bad_words), words)

    def test_no_pipeline_wordlist(self):
        """Test text."""

        config = self.dedent(
            """
            matrix:
            - name: no_pipeline
              default_encoding: utf-8
              sources:
              - '{temp}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline: null
              dictionary:
                wordlists:
                - '{temp}/mydict.wl'
                output: '{temp}/mydict.dic'
            """
        ).format(temp=self.tempdir)
        self.mktemp('.nopipeline.yml', config, 'utf-8')

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        self.mktemp('mydict.wl', '\n'.join(bad_words), 'utf-8')
        self.mktemp('test.txt', '\n'.join(bad_words + good_words), 'utf-8')
        words = self.spellcheck('.nopipeline.yml')
        self.assertEqual([], words)
