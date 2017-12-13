"""Main."""
from __future__ import unicode_literals
import sys
import argparse
from pyspelling import settings
from pyspelling import Spelling
from pyspelling import __version__


def main():
    """Main."""

    parser = argparse.ArgumentParser(prog='spellcheck', description='Spell checking tool.')
    # Flag arguments
    parser.add_argument('--version', action='version', version=('%(prog)s ' + __version__.version))
    parser.add_argument('--verbose', '-v', action='store_true', default=False, help="verbose.")
    parser.add_argument('--config', '-c', action='store', default='.spelling.yml', help="Spelling config.")
    args = parser.parse_args()

    fail = False
    config = settings.read_config(args.config)
    spelling = Spelling(config, verbose=args.verbose)
    if spelling.check():
        fail = True
    return fail


sys.exit(main())
