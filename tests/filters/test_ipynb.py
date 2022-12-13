"""Test Jupyter Notebook Plugin."""
from .. import util

class TestIpynb(util.PluginTestCase):
    """Test Jupyter Notebook plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: ipynb
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
                d: en_US
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.ipynb
              - pyspelling.filters.markdown
              - pyspelling.filters.html:
                  ignores:
                  - code
                  - pre
             """
        ).format(self.tempdir)
        self.mktemp('.ipynb.yml', config, 'utf-8')

    def test_ipynb(self):
        """Test Jupyter Notebook."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']

        template = self.dedent(
            """
            {{
              "cells": [
                {{
                  "cell_type": "markdown",
                  "id": "53806b6d",
                  "metadata": {{}},
                  "source": [
                    "{}"
                  ]
                }}
              ]
            }}
            """
        ).format(
            ' '.join(bad_words + good_words)
        )

        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.ipynb.yml', bad_words)
