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
        self.assert_spellcheck('.nopipeline.yml', bad_words)

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
        self.assert_spellcheck('.nopipeline.yml', [])


class TestNameGroup(util.PluginTestCase):
    """Test name group behavior."""

    def setup_fs(self):
        """Setup files."""

        good_words = ['yes', 'word']
        self.bad_words1 = ['helo', 'begn']
        self.bad_words2 = ['oleh', 'ngeb']
        self.bad_words3 = ['eolh', 'ngbe']
        self.mktemp('test1.txt', '\n'.join(self.bad_words1 + good_words), 'utf-8')
        self.mktemp('test2.txt', '\n'.join(self.bad_words2 + good_words), 'utf-8')
        self.mktemp('test3.txt', '\n'.join(self.bad_words3 + good_words), 'utf-8')

        config = self.dedent(
            """
            matrix:
            - name: name
              group: group1
              default_encoding: utf-8
              sources:
              - '{temp}/**/test1.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
            # Purposely reuse same name
            - name: name
              group: group2
              default_encoding: utf-8
              sources:
              - '{temp}/**/test2.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
            - name: name3
              group: group1
              default_encoding: utf-8
              sources:
              - '{temp}/**/test3.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
            """
        ).format(temp=self.tempdir)
        self.mktemp('.source.yml', config, 'utf-8')

    def test_all(self):
        """Test all."""

        self.assert_spellcheck('.source.yml', self.bad_words1 + self.bad_words2 + self.bad_words3)

    def test_name(self):
        """Test name works."""

        self.assert_spellcheck('.source.yml', self.bad_words2, names=['name'])

    def test_group(self):
        """Test group works."""

        self.assert_spellcheck('.source.yml', self.bad_words1 + self.bad_words3, groups=['group1'])

    def test_sources(self):
        """Test source override."""

        self.assert_spellcheck('.source.yml', self.bad_words1, names=['name'], sources=[self.tempdir + '/**/test1.txt'])

    def test_sources_invalid(self):
        """Test that source override won't work if multiple names are defined."""

        self.assert_spellcheck(
            '.source.yml', self.bad_words2, names=['name', 'other_name'], sources=[self.tempdir + '/**/test1.txt']
        )
