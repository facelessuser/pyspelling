"""Main."""
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
    parser.add_argument(
        '--jobs', '-j',
        action='store',
        type=int,
        default=None,
        help="Specify the number of spell checker processes to run in parallel."
    )
    parser.add_argument('--config', '-c', action='store', default='', help="Spelling config.")
    parser.add_argument(
        '--source', '-S',
        action='append',
        help="Specify override file pattern. Only applicable when specifying exactly one --name."
    )
    parser.add_argument(
        '--spellchecker', '-s', action='store', default='', help="Choose between aspell and hunspell."
    )
    parser.add_argument(
        '--skip-dict-compile',
        '-x',
        action='store_true',
        help="Skip dictionary compilation if the compiled file already exists."
    )
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
        jobs=args.jobs,
        skip_dict_compile=args.skip_dict_compile
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
    jobs = kwargs.get('jobs', None)
    if jobs is not None and jobs < 0:
        jobs = 1
    skip_dict_compile = kwargs.get('skip_dict_compile', False)

    fail = False
    count = 0
    for results in spellcheck(
        config,
        names=names,
        groups=groups,
        binary=binary,
        checker=spellchecker,
        sources=sources,
        verbose=verbose,
        debug=debug,
        jobs=jobs,
        skip_dict_compile=skip_dict_compile
    ):
        count += 1
        if results.error:
            fail = True
            print(f'ERROR: {results.context} -- {results.error}')
        elif results.words:
            fail = True
            print(f'Misspelled words:\n<{results.category}> {results.context}')
            print('-' * 80)
            for word in results.words:
                print(word)
            print('-' * 80)
            print('')

    if fail:
        print('!!!Spelling check failed!!!')
    else:
        print('Spelling check passed :)')

    return fail


if __name__ == "__main__":
    sys.exit(main())
