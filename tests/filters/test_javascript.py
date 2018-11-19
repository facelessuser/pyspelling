"""Test JavaScript plugin."""
from .. import util


class TestJavaScript(util.PluginTestCase):
    """Test JavaScript plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: javascript
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.javascript:
                  jsdocs: true
                  group_comments: true
            """
        ).format(self.tempdir)
        self.mktemp('.javascript.yml', config, 'utf-8')

    def test_javascript(self):
        """Test CPP."""

        bad_docstring = ['helo', 'begn']
        bad_block = ['adn', 'highight']
        bad_comments = ['flga', 'graet']
        bad_comments2 = ['recieve', 'teh']
        bad_words = bad_docstring + bad_block + bad_comments + bad_comments2
        good_words = ['yes', 'word']
        template = self.dedent(
            """
            /**
             * {}
             */
            function Func(arg, arg2) {{
                /* {} */

                var x = 3;
                // {}
                // {}
            }}
            """
        ).format(
            ' '.join(bad_docstring + good_words),
            ' '.join(bad_block + good_words),
            ' '.join(bad_comments + good_words),
            ' '.join(bad_comments2 + good_words)
        )
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.javascript.yml', bad_words)


class TestJavaScriptStrings(util.PluginTestCase):
    """Test JavaScript plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: javascript
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.javascript:
                  jsdocs: true
                  strings: true
                  group_comments: true
            """
        ).format(self.tempdir)
        self.mktemp('.javascript.yml', config, 'utf-8')

    def test_javascript_strings(self):
        """Test CPP."""

        bad_string1 = ['helo', 'begn']
        bad_string2 = ['adn', 'highight']
        bad_words = bad_string1 + bad_string2
        good_words = ['yes', 'word']
        template = self.dedent(
            r"""
            function Func(arg, arg2) {{

              test = "{} \
              {}";

              test2 = "\141\x61\u0061\u{{00000061}}\a";
            }}
            """
        ).format(
            ' '.join(bad_string1 + good_words),
            ' '.join(bad_string2 + good_words)
        )
        bad_words.append('aaaaa')
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.javascript.yml', bad_words)

    def test_javascript_temp_strings(self):
        """Test CPP."""

        bad_string1 = ['helo', 'begn']
        bad_string2 = ['adn', 'highight']
        bad_words = bad_string1 + bad_string2
        good_words = ['yes', 'word']
        template = self.dedent(
            r"""
            function Func(arg, arg2) {{

              test = `{} \
              {}`;

              xxxx = 3;

              test2 = `\x61\u0061\u{{00000061}}\a ${{ {{"test": `value ${{xxxx}} yyyy`}}["test"] }} no`;
            }}
            """
        ).format(
            ' '.join(bad_string1 + good_words),
            ' '.join(bad_string2 + good_words)
        )
        bad_words.extend(['aaaa', 'yyyy'])
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.javascript.yml', bad_words)


class TestJavaScriptGroupedComments(util.PluginTestCase):
    """Test JavaScript plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: javascript
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.javascript:
                  jsdocs: true
                  strings: true
                  group_comments: true
              - pyspelling.filters.context:
                  context_visible_first: true
                  escapes: '\\[\\`]'
                  delimiters:
                  # Ignore multiline content between fences (fences can have 3 or more back ticks)
                  # ```
                  # content
                  # ```
                  - open: '(?s)^(?P<open> *`{{3,}})$'
                    close: '^(?P=open)$'
                  # Ignore text between inline back ticks
                  - open: '(?P<open>`+)'
                    close: '(?P=open)'
            """
        ).format(self.tempdir)
        self.mktemp('.javascript.yml', config, 'utf-8')

    def test_javascript_grouped_comments(self):
        """Test CPP."""

        template = self.dedent(
            r"""
            function Func(arg, arg2) {{

              var test = 3; // what
              // bbbb

              // ```
              // akdjal dlkajdlf dkkjkj
              // skjdl djkjf lslsl
              // ```

              // aaaa
            }}
            """
        )
        bad_words = ['aaaa', 'bbbb']
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.javascript.yml', bad_words)


class TestJavaScriptChained(util.PluginTestCase):
    """Test chained JavaScript plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: javascript
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.text:
              - pyspelling.filters.javascript:
                  jsdocs: true
                  group_comments: true
            """
        ).format(self.tempdir)
        self.mktemp('.javascript.yml', config, 'utf-8')

    def test_javascript_after_text(self):
        """Test javascript after text."""

        bad_docstring = ['helo', 'begn']
        bad_block = ['adn', 'highight']
        bad_comments = ['flga', 'graet']
        bad_comments2 = ['recieve', 'teh']
        bad_words = bad_docstring + bad_block + bad_comments + bad_comments2
        good_words = ['yes', 'word']
        template = self.dedent(
            """
            /**
             * {}
             */
            function Func(arg, arg2) {{
                /* {} */

                var x = 3;
                // {}
                // {}
            }}
            """
        ).format(
            ' '.join(bad_docstring + good_words),
            ' '.join(bad_block + good_words),
            ' '.join(bad_comments + good_words),
            ' '.join(bad_comments2 + good_words)
        )
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.javascript.yml', bad_words)
