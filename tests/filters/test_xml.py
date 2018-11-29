"""Test XML plugin."""
from .. import util


class TestXMLNamespaceNoDefault(util.PluginTestCase):
    """Test XML plugin namespaces without a default namespace."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: xml
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.xml:
                  namespaces:
                    foo: http://me.com/namespaces/foofoo
                    bar: http://me.com/namespaces/foobar
                  ignores:
                  - 'foo|title'
                  - 'bar|*'
                  - '|head'
                  - '*|e2'
                  - 'e3'
            """
        ).format(self.tempdir)
        self.mktemp('.xml.yml', config, 'utf-8')

    def test_xml_namespace_no_default(self):
        """Test XML namespace with no default."""

        template = self.dedent(
            """
            <?xml version="1.0" encoding="UTF-8"?>
            <tag>
              <head>aaaa
              </head>
              <foo:other xmlns:foo="http://me.com/namespaces/foofoo"
                     xmlns:bar="http://me.com/namespaces/foobar">
              <foo:head>
                <foo:title>bbbb</foo:title>
                <bar:title>cccc</bar:title>
              </foo:head>
              <body>
                <foo:e1>dddd</foo:e1>
                <bar:e1>eeee</bar:e1>
                <e1>ffff</e1>
                <foo:e2>gggg</foo:e2>
                <bar:e2>hhhh</bar:e2>
                <e2>iiii</e2>
                <foo:e3>jjjj</foo:e3>
                <bar:e3>kkkk</bar:e3>
                <e3>llll</e3>
              </body>
              </foo:other>
            </tag>
            """
        )

        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.xml.yml', ['dddd', 'ffff'])


class TestXMLRoot(util.PluginTestCase):
    """Test XML plugin namespaces without a default namespace."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: xml
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.xml:
                  namespaces:
                    foo: http://me.com/namespaces/foofoo
                    bar: http://me.com/namespaces/foobar
                  ignores:
                  - ':root > head'
            """
        ).format(self.tempdir)
        self.mktemp('.xml.yml', config, 'utf-8')

    def test_xml_namespace_no_default(self):
        """Test XML namespace with no default."""

        template = self.dedent(
            """
            <?xml version="1.0" encoding="UTF-8"?>
            <tag>
              <head>aaaa
              </head>
              <foo:other xmlns:foo="http://me.com/namespaces/foofoo"
                     xmlns:bar="http://me.com/namespaces/foobar">
              <foo:head>
                <foo:title>bbbb</foo:title>
                <bar:title>cccc</bar:title>
              </foo:head>
              <body>
                <foo:e1>dddd</foo:e1>
                <bar:e1>eeee</bar:e1>
                <e1>ffff</e1>
                <foo:e2>gggg</foo:e2>
                <bar:e2>hhhh</bar:e2>
                <e2>iiii</e2>
                <foo:e3>jjjj</foo:e3>
                <bar:e3>kkkk</bar:e3>
                <e3>llll</e3>
              </body>
              </foo:other>
            </tag>
            """
        )

        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck(
            '.xml.yml',
            ['bbbb', 'cccc', 'dddd', 'eeee', 'ffff', 'gggg', 'hhhh', 'iiii', 'jjjj', 'kkkk', 'llll']
        )


class TestXMLNamespace(util.PluginTestCase):
    """Test XML plugin namespaces."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: xml
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.xml:
                  namespaces:
                    "": http://me.com/namespaces/barbar
                    foo: http://me.com/namespaces/foofoo
                    bar: http://me.com/namespaces/foobar
                  ignores:
                  - 'foo|title'
                  - 'bar|*'
                  - '|head'
                  - '*|e2'
                  - e3
            """
        ).format(self.tempdir)
        self.mktemp('.xml.yml', config, 'utf-8')

    def test_xml_namespace(self):
        """Test XML namespace with no default."""

        template = self.dedent(
            """
            <?xml version="1.0" encoding="UTF-8"?>
            <tag xmlns="http://me.com/namespaces/barbar">
              <head>aaaa
              </head>
              <foo:other xmlns:foo="http://me.com/namespaces/foofoo"
                     xmlns:bar="http://me.com/namespaces/foobar">
              <foo:head>
                <foo:title>bbbb</foo:title>
                <bar:title>cccc</bar:title>
              </foo:head>
              <body>
                <foo:e1>dddd</foo:e1>
                <bar:e1>eeee</bar:e1>
                <e1>ffff</e1>
                <foo:e2>gggg</foo:e2>
                <bar:e2>hhhh</bar:e2>
                <e2>iiii</e2>
                <foo:e3>jjjj</foo:e3>
                <bar:e3>kkkk</bar:e3>
                <e3>llll</e3>
              </body>
              </foo:other>
            </tag>
            """
        )

        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.xml.yml', ['aaaa', 'dddd', 'ffff', 'jjjj'])
