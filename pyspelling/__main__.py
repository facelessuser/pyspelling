"""Main."""
from __future__ import unicode_literals
import sys
import argparse
from pyspelling import settings
from pyspelling import Aspell
from pyspelling import __version__


def run():
    """Main."""

    parser = argparse.ArgumentParser(prog='spellcheck', description='Spell checking tool.')
    # Flag arguments
    parser.add_argument('--version', action='version', version=('%(prog)s ' + __version__.version))
    parser.add_argument('--verbose', '-v', action='count', default=0, help="Verbosity level.")
    parser.add_argument('--name', '-n', action='store', default='', help="Specific spelling task by name to run.")
    parser.add_argument('--binary', '-b', action='store', default='', help="Provide path to Aspell binary.")
    parser.add_argument('--config', '-c', action='store', default='.spelling.yml', help="Spelling config.")
    args = parser.parse_args()

    fail = False
    config = settings.read_config(args.config)
    spelling = Aspell(config, name=args.name, binary=args.binary, verbose=args.verbose)
    for results in spelling.check():
        if results.error:
            fail = True
            print('ERROR: Could not read %s -- %s' % (results.context, results.error))
        elif results.words:
            fail = True
            print('Misspelled words:\n<%s> %s' % (results.category, results.context))
            print('-' * 80)
            for word in results.words:
                print(word)
            print('-' * 80)
            print('')
        elif args.verbose:
            print('CHECK: %s' % results.context)
    return fail


def main():
    """Main entry point."""

    sys.exit(run())


if __name__ == "__main__":
    main()
