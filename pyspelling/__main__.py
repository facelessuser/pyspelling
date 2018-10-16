"""Main."""
from __future__ import unicode_literals
import sys
import argparse
from pyspelling import spellcheck, version


def main():
    """Main."""

    parser = argparse.ArgumentParser(prog='spellcheck', description='Spell checking tool.')
    # Flag arguments
    parser.add_argument('--version', action='version', version=('%(prog)s ' + version))
    parser.add_argument('--verbose', '-v', action='count', default=0, help="Verbosity level.")
    parser.add_argument('--name', '-n', action='store', default='', help="Specific spelling task by name to run.")
    parser.add_argument('--binary', '-b', action='store', default='', help="Provide path to spell checker's binary.")
    parser.add_argument('--config', '-c', action='store', default='.spelling.yml', help="Spelling config.")
    parser.add_argument(
        '--spellchecker', '-s', action='store', default='aspell', help="Choose between aspell and hunspell"
    )
    args = parser.parse_args()

    return run(args.config, args.name, args.binary, args.verbose, args.spellchecker)


def run(config, name='', binary='', verbose=0, spellchecker='aspell'):
    """Run."""

    fail = False
    count = 0
    for results in spellcheck(config, name, binary, verbose, spellchecker):
        count += 1
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
        elif verbose:
            print('CHECK: %s' % results.context)

    return fail


if __name__ == "__main__":
    sys.exit(main())
