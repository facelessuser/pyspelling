"""Test CPP plugin."""
from .. import util


class TestCPP(util.PluginTestCase):
    """Test CPP plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: cpp
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.cpp:
                  group_comments: true
            """
        ).format(self.tempdir)
        self.mktemp('.cpp.yml', config, 'utf-8')

    def test_cpp(self):
        """Test CPP."""

        bad_block = ['helo', 'begn']
        bad_comments = ['flga', 'graet']
        bad_comments2 = ['recieve', 'teh']
        bad_words = bad_block + bad_comments + bad_comments2
        good_words = ['yes', 'word']
        template = self.dedent(
            """
            /*
            {}
            */
            uint8_t func() {{
                uint8_t tsdd = 3;
                // {}
                // {}
                reurn tsdd;
            }}
            """
        ).format(
            '\n'.join(bad_block + good_words),
            ' '.join(bad_comments + good_words),
            ' '.join(bad_comments2 + good_words)
        )
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.cpp.yml', bad_words)


class TestCPPChained(util.PluginTestCase):
    """Test chained CPP plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: cpp
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.text:
              - pyspelling.filters.cpp:
                  group_comments: true
            """
        ).format(self.tempdir)
        self.mktemp('.cpp.yml', config, 'utf-8')

    def test_cpp_after_text(self):
        """Test cpp after text."""

        bad_block = ['helo', 'begn']
        bad_comments = ['flga', 'graet']
        bad_comments2 = ['recieve', 'teh']
        bad_words = bad_block + bad_comments + bad_comments2
        good_words = ['yes', 'word']
        template = self.dedent(
            """
            /*
            {}
            */
            uint8_t func() {{
                uint8_t tsdd = 3;
                // {}
                // {}
                reurn tsdd;
            }}
            """
        ).format(
            '\n'.join(bad_block + good_words),
            ' '.join(bad_comments + good_words),
            ' '.join(bad_comments2 + good_words)
        )
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.cpp.yml', bad_words)
