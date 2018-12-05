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
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  attributes:
                  - alt
                  ignores:
                  - ':is(code, pre)'
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
        self.assert_spellcheck('.html.yml', bad_words)


class TestCSSEscapes(util.PluginTestCase):
    """Test CSS escapes."""

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
                <use xlink:href:colon="images/sprites.svg#icon-redo">bbbb</use>
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

    def test_css_escapes(self):
        """Test css escapes."""

        config = self.dedent(
            """
            matrix:
            - name: html5_css_escapes
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  namespaces:
                    xlink: http://www.w3.org/1999/xlink
                  ignores:
                  - '[xlink|href\\:colon^=images]'
                  - '[xlink|\\68r\\65 f^=other]'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck('.html5.yml', ['aaaa', 'cccc'])


class TestHtml5AttrNamespace(util.PluginTestCase):
    """Test HTML plugin HTML5 attribute and namespace logic."""

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
              hunspell:
                d: en_US
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
        self.assert_spellcheck('.html5.yml', ['bbbb', 'cccc'])

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
              hunspell:
                d: en_US
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
        self.assert_spellcheck('.html5.yml', ['dddd'])

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
              hunspell:
                d: en_US
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
        self.assert_spellcheck('.html5.yml', ['cccc'])


class TestHtml5EmptySelectors(util.PluginTestCase):
    """Test CSS empty selectors."""

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
            <span>aaaa</span>
            <span> <!-- comment --> </span>
            <span>bbbb</span>
            <span>cccc</span>
            <span>  </span>
            <p>dddd</p>
            <span>eeee</span>
            <span>ffff</span>
            <div>
                <p>gggg</p>
                <span>
                </span>
                <p>hhhh</p>
            </div>
            </body>
            </html>
            """
        )

        self.mktemp('test.txt', template, 'utf-8')

    def test_css_empty(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'span:empty + *'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'cccc', 'eeee', 'ffff', 'gggg'
            ]
        )


class TestHtml5OnlySelectors(util.PluginTestCase):
    """Test CSS `nth` selectors."""

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
            <div>
                <p>aaaa</p>
            </div>
            <span>bbbb</span>
            <span>cccc</span>
            <p>dddd</p>
            <span>eeee</span>
            <span>ffff</span>
            <div>
                <p>gggg</p>
                <p>hhhh</p>
            </div>
            </body>
            </html>
            """
        )

        self.mktemp('test.txt', template, 'utf-8')

    def test_css_only_child(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:only-child'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'bbbb', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'hhhh'
            ]
        )

    def test_css_only_type(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:only-of-type'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'bbbb', 'cccc', 'eeee', 'ffff', 'gggg', 'hhhh'
            ]
        )


class TestHtml5NthOfSelectors(util.PluginTestCase):
    """Test CSS `nth` selectors."""

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
            <p>aaaa</p>
            <p>bbbb</p>
            <span class="test">cccc</span>
            <span>dddd</span>
            <span class="test">eeee</span>
            <span>ffff</span>
            <span class="test">gggg</span>
            <p>hhhh</p>
            <p class="test">iiii</p>
            <p>jjjj</p>
            <p class="test">kkkk</p>
            <span>llll</span>
            </body>
            </html>
            """
        )

        self.mktemp('test.txt', template, 'utf-8')

    def test_css_child_of_s(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - ':nth-child(2n + 1 of :is(p, span).test)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'bbbb', 'dddd', 'eeee', 'ffff', 'hhhh', 'iiii', 'jjjj', 'llll'
            ]
        )

    def test_css_child_of_s_vs_schild(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - ':nth-child(-n+3 of p)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'iiii', 'jjjj', 'kkkk', 'llll'
            ]
        )

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:nth-child(-n+3)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'hhhh', 'iiii', 'jjjj', 'kkkk', 'llll'
            ]
        )


class TestHtml5NthSelectors(util.PluginTestCase):
    """Test CSS `nth` selectors."""

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
            <p>aaaa</p>
            <p>bbbb</p>
            <span>cccc</span>
            <span>dddd</span>
            <span>eeee</span>
            <span>ffff</span>
            <span>gggg</span>
            <p>hhhh</p>
            <p>iiii</p>
            <p>jjjj</p>
            <p>kkkk</p>
            <span>llll</span>
            </body>
            </html>
            """
        )

        self.mktemp('test.txt', template, 'utf-8')

    def test_css_first_child(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:first-child'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'bbbb', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'hhhh', 'iiii', 'jjjj', 'kkkk', 'llll'
            ]
        )

    def test_css_nth_type(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:nth-of-type(2n + 1)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'bbbb', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'iiii', 'kkkk', 'llll'
            ]
        )

    def test_css_nth_complex_type(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - ':nth-of-type(2n + 1):is(p, span)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'bbbb', 'dddd', 'ffff', 'iiii', 'kkkk', 'llll'
            ]
        )

    def test_css_nth_odd(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:nth-child(odd)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'bbbb', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'hhhh', 'jjjj', 'llll'
            ]
        )

    def test_css_nth_even(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:nth-child(even)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'iiii', 'kkkk', 'llll'
            ]
        )

    def test_css_nth_child_bad(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:nth-child(-2)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'bbbb', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'hhhh', 'iiii', 'jjjj', 'kkkk', 'llll'
            ]
        )

    def test_css_nth_child1(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:nth-child(2)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'hhhh', 'iiii', 'jjjj', 'kkkk', 'llll'
            ]
        )

    def test_css_nth_child2(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:nth-child(9n - 1)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'bbbb', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'iiii', 'jjjj', 'kkkk', 'llll'
            ]
        )

    def test_css_nth_child3(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:nth-child(2n + 1)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'bbbb', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'hhhh', 'jjjj', 'llll'
            ]
        )

    def test_css_nth_last_type(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:nth-last-of-type(2n + 1)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'jjjj', 'hhhh', 'llll'
            ]
        )

    def test_css_nth_last_child(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:nth-last-child(2n + 1)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'iiii', 'kkkk', 'llll'
            ]
        )

    def test_css_first_type(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'span:first-of-type'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'bbbb', 'dddd', 'eeee', 'ffff', 'gggg', 'hhhh', 'iiii', 'jjjj', 'kkkk', 'llll'
            ]
        )

    def test_css_last_child(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'span:last-child'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'bbbb', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'hhhh', 'iiii', 'jjjj', 'kkkk'
            ]
        )

    def test_css_last_type(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:last-of-type'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'bbbb', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'hhhh', 'iiii', 'jjjj', 'llll'
            ]
        )


class TestHtml5AdvancedSelectors(util.PluginTestCase):
    """Test advanced CSS selectors."""

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
              <div class="aaaa">aaaa
                  <p class="bbbb">bbbb</p>
                  <p class="cccc">cccc</p>
                  <p class="dddd">dddd</p>
                  <div class="eeee">eeee
                  <div class="ffff">ffff
                  <div class="gggg">gggg
                      <p class="hhhh">hhhh</p>
                      <p class="iiii zzzz">iiii</p>
                      <p class="jjjj">jjjj</p>
                      <div class="kkkk">kkkk
                          <p class="llll zzzz">llll</p>
                      </div>
                  </div>
                  </div>
                  </div>
              </div>
            </body>
            </body>
            </html>
            """
        )

        self.mktemp('test.txt', template, 'utf-8')

    def test_css_parents(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'body div.gggg > p.zzzz'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'bbbb', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'hhhh', 'jjjj', 'kkkk', 'llll'
            ]
        )

    def test_css_siblings(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p.bbbb ~ div div.gggg > p.hhhh + p'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'bbbb', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'hhhh', 'jjjj', 'kkkk', 'llll'
            ]
        )

    def test_css_pseudo(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p.bbbb ~ div > div > div :not(p.hhhh + .zzzz)'
                  - 'p:is(.bbbb + .cccc)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'bbbb', 'dddd', 'eeee', 'ffff', 'gggg', 'iiii'
            ]
        )

    def test_css_nested_pseudo(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:is(:not(.zzzz), .iiii)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'eeee', 'ffff', 'gggg', 'kkkk', 'llll'
            ]
        )

    def test_has_pseudo(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'div:not(.aaaa):has(.kkkk > p.llll)'
                  - 'p:has(+ .dddd:has(+ div .jjjj))'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'bbbb', 'dddd'
            ]
        )

    def test_has_pseudo2(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'p:has(~ .jjjj)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'bbbb', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'jjjj', 'kkkk', 'llll'
            ]
        )


class TestHtml5AdvancedSelectors2(util.PluginTestCase):
    """Test advanced CSS selectors."""

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
              <div class="aaaa">aaaa
                  <p class="bbbb">bbbb</p>
              </div>
              <div class="cccc">cccc
                  <p class="dddd">dddd</p>
              </div>
              <div class="eeee">eeee
                  <p class="ffff">ffff</p>
              </div>
              <div class="gggg">gggg
                  <p class="hhhh">hhhh</p>
              </div>
              <div class="iiii">iiii
                  <p class="jjjj">jjjj</p>
                  <span></span>
              </div>
            </body>
            </body>
            </html>
            """
        )

        self.mktemp('test.txt', template, 'utf-8')

    def test_has_list(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'div:has(> .bbbb, .ffff, .jjjj)'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'cccc', 'dddd', 'gggg', 'hhhh'
            ]
        )

    def test_not_has_list(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'div:has(> :not(.bbbb, .ffff, .jjjj))'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'bbbb', 'eeee', 'ffff'
            ]
        )

    def test_not_has_list2(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'div:not(:has(> .bbbb, .ffff, .jjjj))'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'aaaa', 'bbbb', 'eeee', 'ffff', 'iiii', 'jjjj'
            ]
        )

    def test_not_not(self):
        """Test HTML."""

        config = self.dedent(
            """
            matrix:
            - name: html_css
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.html:
                  mode: html5
                  ignores:
                  - 'div:not(:not(.aaaa))'
            """
        ).format(self.tempdir)
        self.mktemp('.html5.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.html5.yml', [
                'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'hhhh', 'iiii', 'jjjj'
            ]
        )


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
              hunspell:
                d: en_US
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
        self.assert_spellcheck('.html5lib.yml', bad_words)


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
              hunspell:
                d: en_US
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
        self.assert_spellcheck('.xhtml.yml', bad_words)


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
              hunspell:
                d: en_US
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
        self.assert_spellcheck('.html.yml', bad_words)
