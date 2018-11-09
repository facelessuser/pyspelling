"""Test Office Open XML plugin."""
from .. import util


class TestOOOXMLFilter(util.PluginTestCase):
    """Test Office Open XML files."""

    def test_docx(self):
        """Test `docx` files."""

        config = self.dedent(
            """
            matrix:
            - name: docx
              sources:
              - 'tests/**/*.docx'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.ooxml
            """
        ).format(self.tempdir)
        self.mktemp('.docx.yml', config, 'utf-8')
        self.assert_spellcheck('.docx.yml', ['tihs', 'smoe', 'txet'])

    def test_pptx(self):
        """Test `pptx` files."""

        config = self.dedent(
            """
            matrix:
            - name: pptx
              sources:
              - 'tests/**/*.pptx'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.ooxml
            """
        ).format(self.tempdir)
        self.mktemp('.pptx.yml', config, 'utf-8')
        self.assert_spellcheck('.pptx.yml', ['tihs', 'smoe', 'txet'])

    def test_xlsx(self):
        """Test `xlsx` files."""

        config = self.dedent(
            """
            matrix:
            - name: xlsx
              sources:
              - 'tests/**/*.xlsx'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.ooxml
            """
        ).format(self.tempdir)
        self.mktemp('.xlsx.yml', config, 'utf-8')
        self.assert_spellcheck('.xlsx.yml', ['tihs', 'smoe', 'txet'])

    def test_docx_chained(self):
        """Test `docx` chained files."""

        config = self.dedent(
            """
            matrix:
            - name: docx
              default_encoding: latin-1
              sources:
              - 'tests/**/*.docx'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.text
              - pyspelling.filters.ooxml
            """
        ).format(self.tempdir)
        self.mktemp('.docx.yml', config, 'utf-8')
        self.assert_spellcheck('.docx.yml', ['tihs', 'smoe', 'txet'])
