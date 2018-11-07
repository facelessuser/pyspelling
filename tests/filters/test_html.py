"""Test HTML plugin."""
from .. import util


class TestHTML(util.PluginTestCase):
    """Test HTML plugin with default `lxml` (HTML) mode."""

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
                  - ':matches(code, pre)'
                  - 'span:matches(.some-class, #some-id)'
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


class TestHtml5AttrNamespace(util.PluginTestCase):
    """Test HTML plugin HTML5 namespace logic."""

    def setup_fs(self):
        """Setup file system."""

        template = self.dedent(
            """
            <!DOCTYPE html>
            <html>
            <head>
              <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            </head>
            <body>
              <h1>A contrived example</h1>
              <svg viewBox="0 0 20 32" class="icon icon-1" data1="1-20-40-50">
                <use xlink:href="images/sprites.svg#icon-undo">aaaa</use>
              </svg>
              <svg viewBox="0 0 30 32" class="icon icon-2" data1="1-20-60-50">
                <use xlink:href="images/sprites.svg#icon-redo">bbbb</use>
              </svg>
              <svg viewBox="0 0 40 32" class="icon icon-3" data="70-20-30-50">
                <use xlink:href="images/sprites.svg#icon-forward">cccc</use>
              </svg>
              <svg viewBox="0 0 50 32" class="icon icon-4" data="100-20-80-50">
                <use xlink:href="other/sprites.svg#icon-reply">dddd</use>
              </svg>
            </body>
            </html>
            """
        )

        self.mktemp('test.txt', template, 'utf-8')

    def test_html_attr_namespace1(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html5_attr_ns
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  namespaces:
                    xlink: http://www.w3.org/1999/xlink
                  ignores:
                  - '[xlink|href$=undo]'
                  - '[xlink|href^=other]'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        words = self.spellcheck('.html5.yml')
        self.assertEqual(sorted(['bbbb', 'cccc']), words)

    def test_html_attr_namespace2(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html5_attr_ns
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  namespaces:
                    xlink: http://www.w3.org/1999/xlink
                  ignores:
                  - '[xlink|href*=forw]'
                  - '[xlink|href="images/sprites.svg#icon-redo"]'
                  - '[viewbox~=20]'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        words = self.spellcheck('.html5.yml')
        self.assertEqual(sorted(['dddd']), words)

    def test_html_attr_namespace3(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html5_attr_ns
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  namespaces:
                    xlink: http://www.w3.org/1999/xlink
                  ignores:
                  - '[data1]'
                  - '[data|=100]'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        words = self.spellcheck('.html5.yml')
        self.assertEqual(sorted(['cccc']), words)


class TestHTML5LIB(util.PluginTestCase):
    """Test HTML plugin with `html5lib`."""

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
                  mode: html5
                  attributes:
                  - alt
                  ignores:
                  - code
                  - pre
                  - span.some-class
                  - span#some-id
            """
        ).format(self.tempdir)
        self.mktemp('.html5lib.yml', config, 'utf-8')

    def test_html5lib(self):
        """Test `html5lib`."""

        bad_comment_words = ['helo', 'begn']
        bad_content_words = ['flga', 'graet']
        bad_attr_words = ['recieve', 'teh']
        bad_words = bad_comment_words + bad_content_words + bad_attr_words
        good_words = ['yes', 'word']

        template = self.dedent(
            """
            <html>
            <head>
            <script>
            ffffff
            </script>
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
        words = self.spellcheck('.html5lib.yml')
        self.assertEqual(sorted(bad_words), words)


class TestXHTML(util.PluginTestCase):
    """Test HTML plugin with `xml` mode."""

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
                  mode: xhtml
                  attributes:
                  - alt
                  ignores:
                  - code
                  - pre
                  - span.some-class
                  - span#some-id
            """
        ).format(self.tempdir)
        self.mktemp('.xhtml.yml', config, 'utf-8')

    def test_xhtml(self):
        """Test XHTML."""

        bad_comment_words = ['helo', 'begn']
        bad_content_words = ['flga', 'graet']
        bad_attr_words = ['recieve', 'teh']
        bad_words = bad_comment_words + bad_content_words + bad_attr_words
        good_words = ['yes', 'word']

        template = self.dedent(
            """
            <?xml version="1.0" encoding="UTF-8"?>
            <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
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
        words = self.spellcheck('.xhtml.yml')
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
