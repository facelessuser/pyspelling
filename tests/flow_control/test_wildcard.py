"""Wildcard test."""
from .. import util


class TestWildcard(util.PluginTestCase):
    """Test wildcard plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            r"""
            matrix:
            - name: python
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.python:
                  group_comments: true
              - pyspelling.flow_control.wildcard:
                  allow:
                  - py-comment
              - pyspelling.filters.context:
                  context_visible_first: true
                  delimiters:
                  # Ignore lint (noqa) and coverage (pragma) as well as shebang (#!)
                  - open: '^(?: *(?:noqa\b|pragma: no cover)|!)'
                    close: '$'
                  # Ignore Python encoding string -*- encoding stuff -*-
                  - open: '^ *-\*-'
                    close: '-\*-$'
              - pyspelling.filters.context:
                  context_visible_first: true
                  escapes: '\\[\\`]'
                  delimiters:
                  # Ignore multiline content between fences (fences can have 3 or more back ticks)
                  # ```
                  # content
                  # ```
                  - open: '(?s)^(?P<open> *`{{3,}})$'
                    close: '^(?P=open)$'
                  # Ignore text between inline back ticks
                  - open: '(?P<open>`+)'
                    close: '(?P=open)'
            """
        ).format(self.tempdir)
        self.mktemp('.wildcard.yml', config, 'utf-8')

    def test_wildcard(self):
        """Test wildcard."""

        bad_words = ['helo', 'begn']
        good_words = ['yes', 'word']
        template = self.dedent(
            """
            #!/usr/bin/env python
            # -*- coding: utf-8 -*-
            \"""
            #! {}
            \"""
            def function():  # noqa
                # ```
                # alsjf alsk
                # eurpoq qeiew
                # ```
            """
        ).format(
            '\n'.join(bad_words + good_words)
        )
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.wildcard.yml', bad_words)
