"""Main."""
import json
import sys
import argparse
from pyspelling import spellcheck, __version__


def main():
    """Main."""

    parser = argparse.ArgumentParser(prog='pyspelling', description='Spell checking tool.')
    # Flag arguments
    parser.add_argument('--version', action='version', version=('%(prog)s ' + __version__))
    parser.add_argument('--debug', action='store_true', default=False, help=argparse.SUPPRESS)
    parser.add_argument('--verbose', '-v', action='count', default=0, help="Verbosity level.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--name', '-n', action='append', help="Specific spelling task by name to run.")
    group.add_argument('--group', '-g', action='append', help="Specific spelling task group to run.")
    parser.add_argument('--binary', '-b', action='store', default='', help="Provide path to spell checker's binary.")
    parser.add_argument('--config', '-c', action='store', default='', help="Spelling config.")
    parser.add_argument(
        '--source', '-S',
        action='append',
        help="Specify override file pattern. Only applicaple when specifying exactly one --name."
    )
    parser.add_argument(
        '--spellchecker', '-s', action='store', default='', help="Choose between aspell and hunspell"
    )
    parser.add_argument('--json', action='store_true', default=False, help="Output result in JSON.")
    args = parser.parse_args()

    return run(
        args.config,
        names=args.name,
        groups=args.group,
        binary=args.binary,
        spellchecker=args.spellchecker,
        sources=args.source,
        verbose=args.verbose,
        debug=args.debug,
        tojson=args.json
    )


def run(config, **kwargs):
    """Run."""

    names = kwargs.get('names', [])
    groups = kwargs.get('groups', [])
    binary = kwargs.get('binary', '')
    spellchecker = kwargs.get('spellchecker', '')
    verbose = kwargs.get('verbose', 0)
    sources = kwargs.get('sources', [])
    debug = kwargs.get('debug', False)
    tojson = kwargs.get('tojson', False)

    fail = False
    count = 0

    json_data = {}

    for results in spellcheck(
        config,
        names=names,
        groups=groups,
        binary=binary,
        checker=spellchecker,
        sources=sources,
        verbose=verbose,
        debug=debug
    ):
        count += 1
        if results.error:
            fail = True
            print('ERROR: %s -- %s' % (results.context, results.error))
        elif results.words:
            fail = True
            if tojson:
                if results.context in json_data:
                    json_data[results.context].extend(results.words)
                else:
                    json_data[results.context]=(results.words)
            else:
                print('Misspelled words:\n<%s> %s' % (results.category, results.context))
                print('-' * 80)
                for word in results.words:
                    print(word)
                print('-' * 80)
                print('')

    if tojson:
        print(json.dumps(json_data, ensure_ascii=False, indent=4))
    else:
        if fail:
            print('!!!Spelling check failed!!!')
        else:
            print('Spelling check passed :)')

    return fail


if __name__ == "__main__":
    sys.exit(main())
