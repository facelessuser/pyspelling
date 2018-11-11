"""Test Markdown plugin."""
from .. import util


class TestMarkdown(util.PluginTestCase):
    """Test Markdown plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: markdown
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.markdown:
                  markdown_extensions:
                  - markdown.extensions.fenced_code:
              - pyspelling.filters.html:
                   ignores:
                   - code
                   - pre
            """
        ).format(self.tempdir)
        self.mktemp('.markdown.yml', config, 'utf-8')

    def test_markdown(self):
        """Test Markdown."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']

        template = self.dedent(
            """
            ## Title

            {}

            Line `slajdl alsjs`

            ```
            skjadf alsdkjls
            ```
            """
        ).format(
            '\n'.join(bad_words + good_words),
        )

        print(template)
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.markdown.yml', bad_words)


class TestMarkdownChained(util.PluginTestCase):
    """Test chained Markdown plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: markdown
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.text:
              - pyspelling.filters.markdown:
                  markdown_extensions:
                  - markdown.extensions.fenced_code:
              - pyspelling.filters.html:
                   ignores:
                   - code
                   - pre
            """
        ).format(self.tempdir)
        self.mktemp('.markdown.yml', config, 'utf-8')

    def test_markdown_after_text(self):
        """Test Markdown."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']

        template = self.dedent(
            """
            ## Title

            {}

            Line `slajdl alsjs`

            ```
            skjadf alsdkjls
            ```
            """
        ).format(
            '\n'.join(bad_words + good_words)
        )

        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.markdown.yml', bad_words)
