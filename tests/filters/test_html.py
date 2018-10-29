"""Test HTML plugin."""
from .. import util


class TestHTML(util.PluginTestCase):
    """Test HTML plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: html
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              pipeline:
              - pyspelling.filters.html:
                   attributes:
                   - alt
                   ignores:
                   - code
                   - pre
                   - span.some-class
                   - span#some-id
            """
        ).format(self.tempdir)
        self.mktemp('.html.yml', config, 'utf-8')

    def test_html(self):
        """Test HTML."""

        bad_comment_words = ['helo', 'begn']
        bad_content_words = ['flga', 'graet']
        bad_attr_words = ['recieve', 'teh']
        bad_words = bad_comment_words + bad_content_words + bad_attr_words
        good_words = ['yes', 'word']

        template = self.dedent(
            """
            <html>
            <head>
            </head>
            <body>
            <!-- {} -->
            <p>{}<code>kjaljw aljwk</code><img src="./image.png" alt="{}"/></p>
            <pre>uouqei euowuw
            </pre>
            <p><span class="some-class">dksj dkjsk</span><span id="some-id">ksjk akjsks</span>
            </body>
            </html>
            """
        ).format(
            '\n'.join(bad_comment_words + good_words),
            ' '.join(bad_content_words + good_words),
            ' '.join(bad_attr_words + good_words)
        )

        self.mktemp('test.txt', template, 'utf-8')
        words = self.spellcheck('.html.yml')
        self.assertEqual(sorted(bad_words), words)


class TestHTMLChained(util.PluginTestCase):
    """Test chained HTML plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: html
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              pipeline:
              - pyspelling.filters.text:
              - pyspelling.filters.html:
                   attributes:
                   - alt
                   ignores:
                   - code
                   - pre
                   - span.some-class
                   - span#some-id
            """
        ).format(self.tempdir)
        self.mktemp('.html.yml', config, 'utf-8')

    def test_html_after_text(self):
        """Test HTML."""

        bad_comment_words = ['helo', 'begn']
        bad_content_words = ['flga', 'graet']
        bad_attr_words = ['recieve', 'teh']
        bad_words = bad_comment_words + bad_content_words + bad_attr_words
        good_words = ['yes', 'word']

        template = self.dedent(
            """
            <html>
            <head>
            </head>
            <body>
            <!-- {} -->
            <p>{}<code>kjaljw aljwk</code><img src="./image.png" alt="{}"/></p>
            <pre>uouqei euowuw
            </pre>
            <p><span class="some-class">dksj dkjsk</span><span id="some-id">ksjk akjsks</span>
            </body>
            </html>
            """
        ).format(
            '\n'.join(bad_comment_words + good_words),
            ' '.join(bad_content_words + good_words),
            ' '.join(bad_attr_words + good_words)
        )

        self.mktemp('test.txt', template, 'utf-8')
        words = self.spellcheck('.html.yml')
        self.assertEqual(sorted(bad_words), words)
