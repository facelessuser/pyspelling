"""Main."""
import sys
import shutil
import time
import argparse
from pyspelling import spellcheck, __version__


class Progress:
    """
    Render per file progress of spelling tasks.

    On a terminal, a single status line is redrawn in place. Otherwise (e.g. CI logs),
    a plain line is printed every 10% so the log is not flooded.
    """

    def __init__(self, stream=None):
        """Initialize."""

        self.stream = sys.stderr if stream is None else stream
        isatty = getattr(self.stream, 'isatty', None)
        self.tty = bool(isatty and isatty())
        self.line = ''
        self.name = ''
        self.total = 0
        self.failed = 0
        self.start = 0.0
        self.bucket = 0

    def __call__(self, name, current, total, filename, failed):
        """Report progress of a task."""

        if current == 0:
            self.name = name
            self.total = total
            self.failed = 0
            self.start = time.monotonic()
            self.bucket = 0
            if total == 0:
                self._write_line(self._summary())
            elif self.tty:
                self._draw(f'[{name}] 0/{total} files (0%)')
            return

        if failed:
            self.failed += 1

        if current >= total:
            self._write_line(self._summary())
        elif self.tty:
            percent = current * 100 // total
            self._draw(f'[{name}] {current}/{total} files ({percent}%) ', filename)
        else:
            bucket = current * 10 // total
            if bucket != self.bucket:
                self.bucket = bucket
                self._write_line(f'[{self.name}] {current}/{total} files')

    def _summary(self):
        """Get the summary line of the current task."""

        elapsed = time.monotonic() - self.start
        files = 'file' if self.total == 1 else 'files'
        return f'[{self.name}] {self.total} {files} checked, {self.failed} with errors ({elapsed:.1f}s)'

    def _draw(self, text, filename=''):
        """Draw the status line in place, truncating the file name to fit the terminal."""

        if filename:
            room = shutil.get_terminal_size().columns - len(text) - 1
            if room <= 3:
                filename = ''
            elif len(filename) > room:
                filename = '...' + filename[-(room - 3):]
        self.line = text + filename
        self.redraw()

    def _write_line(self, text):
        """Write a permanent line, replacing the status line if one is shown."""

        self.clear()
        self.line = ''
        self.stream.write(text + '\n')
        self.stream.flush()

    def clear(self):
        """Erase the status line so other output can be printed."""

        if self.tty and self.line:
            self.stream.write('\r\033[K')
            self.stream.flush()

    def redraw(self):
        """Draw the status line again after other output was printed."""

        if self.tty and self.line:
            self.stream.write('\r\033[K' + self.line)
            self.stream.flush()



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
        help=(
            "Specify the number of spell checker processes to run in parallel. "
            "Using 0 will utilize the maximum number of cores."
        )
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
    parser.add_argument(
        '--progress',
        '-p',
        action='store_true',
        help="Show per file progress on stderr. Ignored when --verbose is used."
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
        skip_dict_compile=args.skip_dict_compile,
        progress=args.progress
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
    # Verbose logging prints per file details already and would garble the status line.
    progress = Progress() if kwargs.get('progress', False) and not verbose else None

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
        skip_dict_compile=skip_dict_compile,
        progress=progress
    ):
        count += 1
        if progress is not None and (results.error or results.words):
            progress.clear()
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
        if progress is not None and (results.error or results.words):
            sys.stdout.flush()
            progress.redraw()

    if fail:
        print('!!!Spelling check failed!!!')
    else:
        print('Spelling check passed :)')

    return fail


if __name__ == "__main__":
    sys.exit(main())
