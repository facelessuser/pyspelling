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
        words = self.spellcheck('.javascript.yml')
        self.assertEqual(sorted(bad_words), words)


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
        words = self.spellcheck('.javascript.yml')
        self.assertEqual(sorted(bad_words), words)
