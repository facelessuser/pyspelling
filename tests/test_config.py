"""Test text plugin."""
from . import util
from wcmatch._wcparse import PatternLimitException


class TestGlob(util.PluginTestCase):
    """Test `glob` behavior."""

    def test_glob_limit(self):
        """Test `glob` with a custom limit."""

        config = self.dedent(
            """
            matrix:
            - name: glob
              default_encoding: utf-8
              glob_pattern_limit: 10
              sources:
              - '{}/**/test-{{1..11}}.txt'
              aspell:
                lang: en
                d: en_US
              hunspell:
                d: en_US
              pipeline: null
            """
        ).format(self.tempdir)
        self.mktemp('.glob.yml', config, 'utf-8')
        with self.assertRaises(PatternLimitException):
            self.assert_spellcheck('.glob.yml', [])

    def test_glob_no_limit(self):
        """Test when there is no limit for `glob` expansion patterns."""

        config = self.dedent(
            """
            matrix:
            - name: glob
              default_encoding: utf-8
              glob_pattern_limit: 0
              sources:
              - '{}/**/test-{{1..11}}.txt'
              aspell:
                lang: en
                d: en_US
              hunspell:
                d: en_US
              pipeline: null
            """
        ).format(self.tempdir)
        self.mktemp('.glob.yml', config, 'utf-8')

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        self.mktemp('test-1.txt', '\n'.join(bad_words + good_words), 'utf-8')
        self.assert_spellcheck('.glob.yml', bad_words)


class TestParallel(util.PluginTestCase):
    """Test parallel processing."""

    def test_parallel(self):
        """Test parallel processing."""

        config = self.dedent(
            """
            jobs: 2

            matrix:
            - name: no_pipeline
              default_encoding: utf-8
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
                d: en_US
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.text:
                  convert_encoding: utf-8
            """
        ).format(self.tempdir)
        self.mktemp('.parallel.yml', config, 'utf-8')

        bad_words1 = ['helo', 'begn']
        good_words1 = ['yes', 'word']
        bad_words2 = ['gdbye', 'stopp']
        good_words2 = ['okay', 'good']
        self.mktemp('test1.txt', '\n'.join(bad_words1 + good_words1), 'utf-8')
        self.mktemp('test2.txt', '\n'.join(bad_words2 + good_words2), 'utf-8')
        self.assert_spellcheck('.parallel.yml', bad_words1 + bad_words2)


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
                d: en_US
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
                d: en_US
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
                d: en_US
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
                d: en_US
              hunspell:
                d: en_US
            - name: name3
              group: group1
              default_encoding: utf-8
              sources:
              - '{temp}/**/test3.txt'
              - '{temp}/**/test4.txt'
              aspell:
                lang: en
                d: en_US
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

    def test_no_sources(self):
        """Test missing source match raises a `ValueError`."""

        config = self.dedent(
            """
            matrix:
            - name: name
              group: group1
              default_encoding: utf-8
              sources:
              - '{temp}/**/test4.txt'
              aspell:
                lang: en
                d: en_US
              hunspell:
                d: en_US
            """
        ).format(temp=self.tempdir)
        self.mktemp('.nosource.yml', config, 'utf-8')
        with self.assertRaises(RuntimeError) as excctxt:
            self.assert_spellcheck('.nosource.yml', [])
        self.assertIn('test4.txt', str(excctxt.exception))

    def test_sources(self):
        """Test source override."""

        self.assert_spellcheck('.source.yml', self.bad_words1, names=['name'], sources=[self.tempdir + '/**/test1.txt'])

    def test_sources_invalid(self):
        """Test that source override won't work if multiple names are defined."""

        self.assert_spellcheck(
            '.source.yml', self.bad_words2, names=['name', 'other_name'], sources=[self.tempdir + '/**/test1.txt']
        )

    def test_no_matrix(self):
        """Test a `ValueError` is raised if the configuration has no matrix."""

        config = self.dedent(
            """
            something: []
            """
        )

        self.mktemp('.source.yml', config, 'utf-8')
        with self.assertRaises(KeyError):
            self.assert_spellcheck('.source.yml', [])

    def test_bad_name(self):
        """Test bad name."""

        config = self.dedent(
            """
            matrix:
            - name: other
            """
        )
        self.mktemp('.source.yml', config, 'utf-8')
        with self.assertRaises(ValueError):
            self.assert_spellcheck('.source.yml', [], names=['name'])

    def test_no_name(self):
        """Test no name."""

        config = self.dedent(
            """
            matrix: []
            """
        )
        self.mktemp('.source.yml', config, 'utf-8')
        with self.assertRaises(ValueError):
            self.assert_spellcheck('.source.yml', [])

    def test_too_many_filter_names(self):
        """Test too many filter names."""

        config = self.dedent(
            """
            matrix:
            - name: too_many_pipeline_names
              default_encoding: utf-8
              sources:
              - '{temp}/**/*.txt'
              aspell:
                lang: en
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                # should be indented more
                name2: 1
            """.format(temp=self.tempdir)
        )
        self.mktemp('.source.yml', config, 'utf-8')
        self.mktemp('test.txt', '', 'utf-8')
        with self.assertRaises(ValueError):
            self.assert_spellcheck('.source.yml', [])


class TestSkipDictionary(util.PluginTestCase):
    """Test no pipeline."""

    def test_skip(self):
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
                d: en_US
              hunspell:
                d: en_US
              pipeline: null
              dictionary:
                wordlists:
                - '{temp}/mydict.wl'
                output: '{temp}/mydict.dic'
            """
        ).format(temp=self.tempdir)
        self.mktemp('.skip_compile.yml', config, 'utf-8')

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        self.mktemp('mydict.wl', '\n'.join(bad_words), 'utf-8')
        self.mktemp('test.txt', '\n'.join(bad_words + good_words), 'utf-8')
        self.assert_spellcheck('.skip_compile.yml', ['helo', 'begn'], skip_dict_compile=True)

    def test_compile_once(self):
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
                d: en_US
              hunspell:
                d: en_US
              pipeline: null
              dictionary:
                wordlists:
                - '{temp}/mydict.wl'
                output: '{temp}/mydict.dic'
            """
        ).format(temp=self.tempdir)
        self.mktemp('.skip_compile.yml', config, 'utf-8')

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        self.mktemp('mydict.wl', '\n'.join(bad_words), 'utf-8')
        self.mktemp('test.txt', '\n'.join(bad_words + good_words), 'utf-8')
        # For this to work, we need to run on either Hunspell or Aspell, not both as the dictionary
        # will be overwritten with the format for the wrong spell checker.
        self.assert_spellcheck('.skip_compile.yml', [], skip_dict_compile=False, only_one=True)
        self.assert_spellcheck('.skip_compile.yml', [], skip_dict_compile=True, only_one=True)
