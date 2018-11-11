"""Test stylesheets plugin."""
from .. import util


class TestStylesheetsCSS(util.PluginTestCase):
    """Test stylesheets CSS plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.stylesheets:
                  stylesheets: css
                  group_comments: true
            """
        ).format(self.tempdir)
        self.mktemp('.stylesheets_css.yml', config, 'utf-8')

    def test_stylesheets_css(self):
        """Test stylesheets CSS."""

        bad_words = ['flga', 'graet']
        good_words = ['yes', 'word']
        template = self.dedent(
            """
            /*
            {}
            */
            p#id.class, p.other_id.class {{
                color: white;
            }}
            """
        ).format(
            '\n'.join(bad_words + good_words)
        )
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.stylesheets_css.yml', bad_words)


class TestStylesheetsSCSS(util.PluginTestCase):
    """Test stylesheets SCSS plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: scss
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.stylesheets:
                  stylesheets: scss
                  group_comments: true
            """
        ).format(self.tempdir)
        self.mktemp('.stylesheets_scss.yml', config, 'utf-8')

    def test_stylesheets_scss(self):
        """Test stylesheets SCSS."""

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
            @mixin cover {{
              $color: red;
              // {}
              // {}
              @for $i from 1 through 5 {{
                &.bg-cover#{{$i}} {{ background-color: adjust-hue($color, 15deg * $i) }}
              }}
            }}
            .wrapper {{ @include cover }}
            """
        ).format(
            '\n'.join(bad_block + good_words),
            ' '.join(bad_comments + good_words),
            ' '.join(bad_comments2 + good_words)
        )
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.stylesheets_scss.yml', bad_words)


class TestStylesheetsSASS(util.PluginTestCase):
    """Test stylesheets SASS plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: scss
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.stylesheets:
                  stylesheets: sass
                  group_comments: true
            """
        ).format(self.tempdir)
        self.mktemp('.stylesheets_sass.yml', config, 'utf-8')

    def test_stylesheets_sass(self):
        """Test stylesheets SASS."""

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
            =cover
              $color: red
              // {}
              // {}
              @for $i from 1 through 5
                &.bg-cover#{{$i}}
                  background-color: adjust-hue($color, 15deg * $i)
            .wrapper
              +cover
            """
        ).format(
            '\n'.join(bad_block + good_words),
            ' '.join(bad_comments + good_words),
            ' '.join(bad_comments2 + good_words)
        )
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.stylesheets_sass.yml', bad_words)


class TestStylesheetsCSSChained(util.PluginTestCase):
    """Test chained stylesheets CSS plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.text:
              - pyspelling.filters.stylesheets:
                  stylesheets: css
                  group_comments: true
            """
        ).format(self.tempdir)
        self.mktemp('.stylesheets_css.yml', config, 'utf-8')

    def test_stylesheets_css_after_text(self):
        """Test stylesheets CSS."""

        bad_words = ['flga', 'graet']
        good_words = ['yes', 'word']
        template = self.dedent(
            """
            /*
            {}
            */
            p#id.class, p.other_id.class {{
                color: white;
            }}
            """
        ).format(
            '\n'.join(bad_words + good_words)
        )
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.stylesheets_css.yml', bad_words)
