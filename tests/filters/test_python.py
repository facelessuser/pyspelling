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
              hunspell:
                d: en_US
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
        self.assert_spellcheck('.python.yml', bad_words)


class TestPythonStrings(util.PluginTestCase):
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
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.python:
                  strings: true
                  string_types: bfru
                  group_comments: true
            """
        ).format(self.tempdir)
        self.mktemp('.pystrings.yml', config, 'utf-8')

    def test_python_continue(self):
        """Test strings with line continuation."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        template = self.dedent(
            r"""
            def function():
                test = "{} \tthe\
                aaaa"
            """
        ).format(
            ' '.join(bad_words + good_words)
        )
        bad_words.append('aaaa')
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.pystrings.yml', bad_words)

    def test_python_raw(self):
        """Test Python raw strings."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        template = self.dedent(
            r"""
            def function():
                test = r"{} \tthe"
            """
        ).format(
            ' '.join(bad_words + good_words)
        )
        bad_words.append('tthe')
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.pystrings.yml', bad_words)

    def test_python_unicode(self):
        """Test Python Unicode strings."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        template = self.dedent(
            r"""
            def function():
                test = "{} \141\x61\u0061\U00000061\N{{LATIN SMALL LETTER A}}"
            """
        ).format(
            ' '.join(bad_words + good_words)
        )
        bad_words.append('aaaaa')
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.pystrings.yml', bad_words)

    def test_python_bytes(self):
        """Test Python byte strings."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        template = self.dedent(
            r"""
            def function():
                test = b"\x03\x03\x02{} \tthe \141\541\141\541\x03\xff\x03\x02"
            """
        ).format(
            '\\x03'.join(bad_words + good_words)
        )
        bad_words.append('aaaa')
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.pystrings.yml', bad_words)

    def test_python_raw_bytes(self):
        """Test Python raw byte strings."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        template = self.dedent(
            r"""
            def function():
                test = rb"{} \tthe \xff"
            """
        ).format(
            ' '.join(bad_words + good_words)
        )
        bad_words.extend(['tthe', 'xff'])
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.pystrings.yml', bad_words)

    def test_python_format(self):
        """Test Python format strings."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        template = self.dedent(
            r"""
            def function():
                aaaa = "text"
                test = f"{} \tthe {{aaaa}}"
            """
        ).format(
            ' '.join(bad_words + good_words)
        )

        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.pystrings.yml', bad_words)

    def test_python_raw_format(self):
        """Test Python raw format strings."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        template = self.dedent(
            r"""
            def function():
                aaaa = "text"
                test = fr"{} \tthe {{aaaa}}"
            """
        ).format(
            ' '.join(bad_words + good_words)
        )

        bad_words.append('tthe')

        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.pystrings.yml', bad_words)


class TestPythonStringAllow(util.PluginTestCase):
    """Test Python allow filter."""

    def setup_fs(self):
        """Setup."""

        template = self.dedent(
            r"""
            def func():
                s0 =   "aaaa"
                s1 =  u"bbbb"
                s2 =  b"cccc"
                s3 =  f"dddd"
                s4 =  r"eeee"
                s5 =  br"ffff"
                s7 =  fr"gggg"
            """
        )

        self.mktemp('test.txt', template, 'utf-8')

    def test_exclude_unicode(self):
        """Test exclude Unicode."""

        config = self.dedent(
            """
            matrix:
            - name: python
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.python:
                  strings: true
                  string_types: brf
            """
        ).format(self.tempdir)
        self.mktemp('.python.yml', config, 'utf-8')
        self.assert_spellcheck('.python.yml', ['cccc', 'dddd', 'ffff', 'gggg'])

    def test_exclude_bytes(self):
        """Test exclude bytes."""

        config = self.dedent(
            """
            matrix:
            - name: python
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.python:
                  strings: true
                  string_types: urf
            """
        ).format(self.tempdir)
        self.mktemp('.python.yml', config, 'utf-8')
        self.assert_spellcheck('.python.yml', ['aaaa', 'bbbb', 'dddd', 'eeee', 'gggg'])

    def test_exclude_format(self):
        """Test exclude format."""

        config = self.dedent(
            """
            matrix:
            - name: python
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.python:
                  strings: true
                  string_types: bur
            """
        ).format(self.tempdir)
        self.mktemp('.python.yml', config, 'utf-8')
        self.assert_spellcheck('.python.yml', ['aaaa', 'bbbb', 'cccc', 'eeee', 'ffff'])

    def test_exclude_raw(self):
        """Test exclude raw."""

        config = self.dedent(
            """
            matrix:
            - name: python
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.python:
                  strings: true
                  string_types: buf
            """
        ).format(self.tempdir)
        self.mktemp('.python.yml', config, 'utf-8')
        self.assert_spellcheck('.python.yml', ['aaaa', 'bbbb', 'cccc', 'dddd'])

    def test_include_all(self):
        """Test include all."""

        config = self.dedent(
            """
            matrix:
            - name: python
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.python:
                  strings: true
                  string_types: '*'
            """
        ).format(self.tempdir)
        self.mktemp('.python.yml', config, 'utf-8')
        self.assert_spellcheck('.python.yml', ['aaaa', 'bbbb', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg'])

    def test_include_all_raw(self):
        """Test include all raw."""

        config = self.dedent(
            """
            matrix:
            - name: python
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.python:
                  strings: true
                  string_types: 'r*'
            """
        ).format(self.tempdir)
        self.mktemp('.python.yml', config, 'utf-8')
        self.assert_spellcheck('.python.yml', ['eeee', 'ffff', 'gggg'])

    def test_include_all_unicode(self):
        """Test include all Unicode."""

        config = self.dedent(
            """
            matrix:
            - name: python
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.python:
                  strings: true
                  string_types: 'u*'
            """
        ).format(self.tempdir)
        self.mktemp('.python.yml', config, 'utf-8')
        self.assert_spellcheck('.python.yml', ['aaaa', 'bbbb', 'eeee'])


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
              hunspell:
                d: en_US
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
        self.assert_spellcheck('.python.yml', bad_words)
