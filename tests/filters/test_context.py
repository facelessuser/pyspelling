"""Test context plugin."""
from .. import util


class TestContext(util.PluginTestCase):
    """Test context plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: context
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
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
        self.mktemp('.context.yml', config, 'utf-8')

    def test_context(self):
        """Test text."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        template = self.dedent(
            """
            {}
            ```
            djlask dkjsl dksj
            kudk alks
            ```

            Line with `incoretc txet`.
            """
        ).format('\n'.join(bad_words + good_words))
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.context.yml', bad_words)


class TestContextChained(util.PluginTestCase):
    """Test chained context plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: context
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.text:
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
        self.mktemp('.context.yml', config, 'utf-8')

    def test_context_after_text(self):
        """Test text."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        template = self.dedent(
            """
            {}
            ```
            djlask dkjsl dksj
            kudk alks
            ```

            Line with `incoretc txet`.
            """
        ).format('\n'.join(bad_words + good_words))
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.context.yml', bad_words)
