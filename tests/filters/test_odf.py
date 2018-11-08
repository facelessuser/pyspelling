"""Test ODF plugin."""
from .. import util


class TestODFFilter(util.PluginTestCase):
    """Test ODF files."""

    def test_odt(self):
        """Test `odt` files."""

        config = self.dedent(
            """
            matrix:
            - name: odt
              sources:
              - 'tests/**/*.odt'
              aspell:
                lang: en
              pipeline:
              - pyspelling.filters.odf
            """
        ).format(self.tempdir)
        self.mktemp('.odt.yml', config, 'utf-8')
        words = self.spellcheck('.odt.yml')
        self.assertEqual(sorted(['tihs', 'smoe', 'txet']), words)

    def test_fodt(self):
        """Test `fodt` files."""

        config = self.dedent(
            """
            matrix:
            - name: fodt
              sources:
              - 'tests/**/*.fodt'
              aspell:
                lang: en
              pipeline:
              - pyspelling.filters.odf
            """
        ).format(self.tempdir)
        self.mktemp('.fodt.yml', config, 'utf-8')
        words = self.spellcheck('.fodt.yml')
        self.assertEqual(sorted(['tihs', 'smoe', 'txet']), words)

    def test_odp(self):
        """Test `odp` files."""

        config = self.dedent(
            """
            matrix:
            - name: odp
              sources:
              - 'tests/**/*.odp'
              aspell:
                lang: en
              pipeline:
              - pyspelling.filters.odf
            """
        ).format(self.tempdir)
        self.mktemp('.odp.yml', config, 'utf-8')
        words = self.spellcheck('.odp.yml')
        self.assertEqual(sorted(['tihs', 'smoe', 'txet']), words)

    def test_ods(self):
        """Test `ods` files."""

        config = self.dedent(
            """
            matrix:
            - name: ods
              sources:
              - 'tests/**/*.ods'
              aspell:
                lang: en
              pipeline:
              - pyspelling.filters.odf
            """
        ).format(self.tempdir)
        self.mktemp('.ods.yml', config, 'utf-8')
        words = self.spellcheck('.ods.yml')
        self.assertEqual(sorted(['tihs', 'smoe', 'txet']), words)

    def test_odt_chained(self):
        """Test `odt` chained files."""

        config = self.dedent(
            """
            matrix:
            - name: odt
              default_encoding: latin-1
              sources:
              - 'tests/**/*.odt'
              aspell:
                lang: en
              pipeline:
              - pyspelling.filters.text
              - pyspelling.filters.odf
            """
        ).format(self.tempdir)
        self.mktemp('.odt.yml', config, 'utf-8')
        words = self.spellcheck('.odt.yml')
        self.assertEqual(sorted(['tihs', 'smoe', 'txet']), words)

    def test_fodt_chained(self):
        """Test `fodt` chained files."""

        config = self.dedent(
            """
            matrix:
            - name: fodt
              sources:
              - 'tests/**/*.fodt'
              aspell:
                lang: en
              pipeline:
              - pyspelling.filters.text
              - pyspelling.filters.odf
            """
        ).format(self.tempdir)
        self.mktemp('.fodt.yml', config, 'utf-8')
        words = self.spellcheck('.fodt.yml')
        self.assertEqual(sorted(['tihs', 'smoe', 'txet']), words)
