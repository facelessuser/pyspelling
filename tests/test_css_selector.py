"""Test CSS selector library."""
import unittest
import bs4
import html
from pyspelling.util import css_selectors as cs


class TestCssSelectors(unittest.TestCase):
    """Test CSS selectors."""

    def assert_selectors(self, text, select, ignore, ids, comments, ns=None, flags=0):
        """Assert selector matches."""

        soup = bs4.BeautifulSoup(text, 'html5lib')
        c = []
        tag_ids = []

        for el in cs.select(soup, select, ignore, ns, flags):
            self.assertTrue(isinstance(el, (bs4.element.Tag, bs4.Comment)))

            if isinstance(el, bs4.Comment):
                c.append(html.unescape(str(el).strip()))
            else:
                tag_ids.append(el.attrs['id'])

        self.assertEqual(sorted(c), sorted(comments))
        self.assertEqual(sorted(ids), sorted(tag_ids))

    def test_comments(self):
        """Test selectors."""

        text = """
        <!-- before header -->
        <html>
        <head>
        </head>
        <body>
        <!-- comment -->
        <p id="1"><code id="2"></code><img id="3" src="./image.png"/></p>
        <pre id="4"></pre>
        <p><span id="5" class="some-class"></span><span id="some-id"></span></p>
        <pre id="6" class='ignore'>
            <!-- don't ignore -->
        </pre>
        </body>
        </html>
        """

        soup = bs4.BeautifulSoup(text, 'html5lib')
        comments = [str(c).strip() for c in cs.comments(soup, cs.HTML5)]
        self.assertEqual(sorted(comments), sorted(['before header', 'comment', "don't ignore"]))

    def test_is(self):
        """Test selectors."""

        text = """
        <html>
        <head>
        </head>
        <body>
        <!-- comment -->
        <p id="1"><code id="2"></code><img id="3" src="./image.png"/></p>
        <pre id="4"></pre>
        <p><span id="5" class="some-class"></span><span id="some-id"></span></p>
        <pre id="6" class='ignore'>
            <!-- don't ignore -->
        </pre>
        </body>
        </html>
        """

        self.assert_selectors(
            text,
            ':is(code, pre), span:matches(.some-class, #some-id)',
            "pre.ignore",
            ['2', '4', '5', 'some-id'],
            ['comment', "don't ignore"],
            flags=cs.COMMENTS
        )

    def test_attributes(self):
        """Test selectors."""

        text = """
        <!DOCTYPE html>
        <html>
        <head>
          <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        </head>
        <body>
          <h1 id="0">A contrived example</h1>
          <svg id="1" viewBox="0 0 20 32" class="icon icon-1" data1="1-20-40-50">
            <use id="2" xlink:href="images/sprites.svg#icon-undo"></use>
          </svg>
          <svg id="3" viewBox="0 0 30 32" class="icon icon-2" data1="1-20-60-50">
            <use id="4" xlink:href:colon="images/sprites.svg#icon-redo"></use>
          </svg>
          <svg id="5" viewBox="0 0 40 32" class="icon icon-3" data="70-20-30-50">
            <use id="6" xlink:href="images/sprites.svg#icon-forward"></use>
          </svg>
          <svg id="7" viewBox="0 0 50 32" class="icon icon-4" data="100-20-80-50">
            <use id="8" xlink:href="other/sprites.svg#icon-reply"></use>
          </svg>
        </body>
        </html>
        """

        self.assert_selectors(
            text,
            '[xlink|href\\:colon^=images], [xlink|\\68r\\65 f^=other]',
            "",
            ['4', '8'],
            [],
            ns={'xlink': 'http://www.w3.org/1999/xlink'},
            flags=cs.HTML5
        )

        self.assert_selectors(
            text,
            '[xlink|href$=undo],[xlink|href^=other]',
            "",
            ['2', '8'],
            [],
            ns={'xlink': 'http://www.w3.org/1999/xlink'},
            flags=cs.HTML5
        )

        self.assert_selectors(
            text,
            '[xlink|href*=forw],'
            '[xlink|href\\:colon="images/sprites.svg#icon-redo"],'
            '[viewbox~=20]',
            "",
            ['1', '4', '6'],
            [],
            ns={'xlink': 'http://www.w3.org/1999/xlink'},
            flags=cs.HTML5
        )
