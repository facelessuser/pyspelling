"""Spell check with Aspell or Hunspell."""
import os
import importlib
from . import util
from .__meta__ import __version__, __version_info__  # noqa: F401
from . import flow_control
from . import filters
from wcmatch import glob
import codecs
from collections import namedtuple
from concurrent.futures import ProcessPoolExecutor

__all__ = ("spellcheck",)

STEP_ERROR = """Pipeline step in unexpected format: {}

Each pipeline step should be in the form {{key: options: {{}}}} not {{key: {{}}, key2: {{}}}}
"""


def log(text, level, verbose=0):
    """Log level."""

    if verbose >= level:
        print(text)


class Results(namedtuple('Results', ['words', 'context', 'category', 'error'])):
    """Results."""

    def __new__(cls, words, context, category, error=None):
        """Allow defaults."""

        return super().__new__(cls, words, context, category, error)


class SpellChecker:
    """Spell check class."""

    DICTIONARY = 'dictionary.dic'

    def __init__(self, config, binary='', verbose=0, default_encoding='', debug=False):
        """Initialize."""

        # General options
        self.binary = binary if binary else 'aspell'
        self.verbose = verbose
        self.debug = debug
        self.default_encoding = default_encoding

    def log(self, text, level):
        """Log level."""

        log(text, level, verbose=self.verbose)

    def get_error(self, e):
        """Get the error."""

        import traceback

        return traceback.format_exc() if self.debug else str(e)

    def setup_command(self, encoding, options, personal_dict, file_name=None):
        """Setup the command."""

        return []

    def _pipeline_step(self, sources, options, personal_dict, filter_index=1, flow_status=flow_control.ALLOW):
        """Recursively run text objects through the pipeline steps."""

        for source in sources:
            if source._has_error():
                yield source
            elif not source._is_bytes() and filter_index < len(self.pipeline_steps):
                f = self.pipeline_steps[filter_index]
                if isinstance(f, flow_control.FlowControl):
                    err = ''
                    try:
                        status = f._run(source.category)
                    except Exception as e:
                        err = self.get_error(e)
                        yield filters.SourceText('', source.context, '', '', err)
                    if not err:
                        if filter_index < len(self.pipeline_steps):
                            yield from self._pipeline_step(
                                [source], options, personal_dict, filter_index + 1, status
                            )
                else:
                    if flow_status == flow_control.ALLOW:
                        err = ''
                        try:
                            srcs = f._run(source)
                        except Exception as e:
                            err = self.get_error(e)
                            yield filters.SourceText('', source.context, '', '', err)
                        if not err:
                            yield from self._pipeline_step(
                                srcs, options, personal_dict, filter_index + 1
                            )
                    elif flow_status == flow_control.SKIP:
                        yield from self._pipeline_step(
                            [source], options, personal_dict, filter_index + 1
                        )
                    else:
                        # Halted tasks
                        yield source
            else:
                # Binary content
                yield source

    def _spelling_pipeline(self, sources, options, personal_dict):
        """Check spelling pipeline."""

        for source in self._pipeline_step(sources, options, personal_dict):
            # Don't waste time on empty strings
            if source._has_error():
                yield Results([], source.context, source.category, source.error)
            elif not source.text or source.text.isspace():
                continue
            else:
                encoding = source.encoding
                if source._is_bytes():
                    text = source.text
                else:
                    # UTF-16 and UTF-32 don't work well with Aspell and Hunspell,
                    # so encode with the compatible UTF-8 instead.
                    if encoding.startswith(('utf-16', 'utf-32')):
                        encoding = 'utf-8'
                    text = source.text.encode(encoding)
                self.log('', 3)
                self.log(text, 3)
                cmd = self.setup_command(encoding, options, personal_dict)
                self.log("Command: " + str(cmd), 4)

                try:
                    wordlist = util.call_spellchecker(cmd, input_text=text, encoding=encoding)
                    yield Results(
                        [w for w in sorted(set(wordlist.replace('\r', '').split('\n'))) if w],
                        source.context,
                        source.category
                    )
                except Exception as e:  # pragma: no cover
                    err = self.get_error(e)
                    yield Results([], source.context, source.category, err)

    def spell_check_no_pipeline(self, sources, options, personal_dict):
        """Spell check without the pipeline."""

    def compile_dictionary(self, lang, wordlists, output, verbose):
        """Compile user dictionary."""

    @staticmethod
    def get_options(task):
        """Setup spell checker."""

        return {}

    def setup_dictionary(self, task, binary, verbose):
        """Setup dictionary."""

        return None

    def _build_pipeline(self, task):
        """Build up the pipeline."""

        self.pipeline_steps = []
        kwargs = {}
        if self.default_encoding:
            kwargs["default_encoding"] = self.default_encoding

        steps = task.get('pipeline', [])
        if steps is None:
            self.pipeline_steps = None
        else:
            if not steps:
                steps = task.get('filters', [])
                if steps:
                    util.warn_deprecated(
                        "'filters' key in config is deprecated. 'pipeline' should be used going forward."
                    )

            if not steps:
                steps.append('pyspelling.filters.text')

            for step in steps:
                # Retrieve module and module options
                if isinstance(step, dict):
                    if len(step) > 1:
                        raise ValueError(STEP_ERROR.format(str(step)))
                    name, options = next(iter(step.items()))
                else:
                    name = step
                    options = {}
                if options is None:
                    options = {}

                module = self._get_module(name)
                if issubclass(module, filters.Filter):
                    self.pipeline_steps.append(module(options, **kwargs))
                elif issubclass(module, flow_control.FlowControl):
                    if self.pipeline_steps:
                        self.pipeline_steps.append(module(options))
                    else:
                        raise ValueError("Pipeline cannot start with a 'Flow Control' plugin!")
                else:
                    raise ValueError("'%s' is not a valid plugin!" % name)

    def _get_module(self, module):
        """Get module."""

        if isinstance(module, str):
            mod = importlib.import_module(module)
        for name in ('get_plugin', 'get_filter'):
            attr = getattr(mod, name, None)
            if attr is not None:
                break
            if name == 'get_filter':
                util.warn_deprecated("'get_filter' is deprecated. Plugins should use 'get_plugin'.")
        if not attr:
            raise ValueError("Could not find the 'get_plugin' function in module '%s'!" % module)
        return attr()

    def get_source(self, f):
        """Get the source."""

        if self.pipeline_steps:
            try:
                source = self.pipeline_steps[0]._run_first(f)
            except Exception as e:
                err = self.get_error(e)
                source = [filters.SourceText('', f, '', '', err)]
        else:
            try:
                if self.default_encoding:
                    encoding = filters.PYTHON_ENCODING_NAMES.get(
                        self.default_encoding, self.default_encoding
                    ).lower()
                    encoding = codecs.lookup(encoding).name
                else:
                    encoding = self.default_encoding
                source = [filters.SourceText('', f, encoding, 'file')]
            except Exception as e:
                err = self.get_error(e)
                source = [filters.SourceText('', f, '', '', err)]
        return source


class Aspell(SpellChecker):
    """Aspell spell check class."""

    def __init__(self, config, binary='', verbose=0, default_encoding='', debug=False):
        """Initialize."""

        super().__init__(config, binary, verbose, default_encoding, debug)
        self.binary = binary if binary else 'aspell'

    @staticmethod
    def get_options(task):
        """Setup spell checker."""

        return task.get('aspell', {})

    @classmethod
    def setup_dictionary(cls, task, binary, verbose):
        """Setup dictionary."""

        dictionary_options = task.get('dictionary', {})
        output = os.path.abspath(dictionary_options.get('output', os.path.abspath(cls.DICTIONARY)))
        aspell_options = task.get('aspell', {})
        lang = aspell_options.get('lang', aspell_options.get('l', 'en'))
        wordlists = dictionary_options.get('wordlists', [])
        if lang and wordlists:
            cls.compile_dictionary(
                binary,
                lang,
                dictionary_options.get('wordlists', []),
                dictionary_options.get('encoding', 'utf-8'),
                output,
                verbose
            )
        else:
            output = None
        return output

    @classmethod
    def compile_dictionary(cls, binary, lang, wordlists, encoding, output, verbose):
        """Compile user dictionary."""

        cmd = [
            binary,
            '--lang', lang,
            '--encoding', codecs.lookup(filters.PYTHON_ENCODING_NAMES.get(encoding, encoding).lower()).name,
            'create',
            'master', output
        ]

        wordlist = ''

        try:
            output_location = os.path.dirname(output)
            if not os.path.exists(output_location):
                os.makedirs(output_location)
            if os.path.exists(output):
                os.remove(output)

            log("Compiling Dictionary...", 1, verbose)
            # Read word lists and create a unique set of words
            words = set()
            for wordlist in wordlists:
                with open(wordlist, 'rb') as src:
                    for word in src.read().split(b'\n'):
                        words.add(word.replace(b'\r', b''))

            # Compile wordlist against language
            util.call(
                cmd,
                input_text=b'\n'.join(sorted(words)) + b'\n'
            )
        except Exception:
            log(cmd, 0, verbose)
            log("Current wordlist: '%s'" % wordlist, 0, verbose)
            log("Problem compiling dictionary. Check the binary path and options.", 0, verbose)
            raise

    def spell_check_no_pipeline(self, sources, options, personal_dict):
        """Spell check without the pipeline."""

        for source in sources:

            if source._has_error():  # pragma: no cover
                yield Results([], source.context, source.category, source.error)

            try:
                with open(source.context, 'rb') as f:
                    content = f.read()
            except Exception as e:  # pragma: no cover
                err = self.get_error(e)
                yield Results([], source.context, source.category, err)

            # Don't waste time on empty string
            if not content or content.isspace():
                continue

            self.log('', 3)
            self.log(content, 3)

            cmd = self.setup_command(source.encoding, options, personal_dict, source.context)
            self.log("Command: " + str(cmd), 4)
            try:
                wordlist = util.call_spellchecker(cmd, input_text=content, encoding=source.encoding)
                yield Results(
                    [w for w in sorted(set(wordlist.replace('\r', '').split('\n'))) if w],
                    source.context,
                    source.category
                )
            except Exception as e:  # pragma: no cover
                err = self.get_error(e)
                yield Results([], source.context, source.category, err)

    def setup_command(self, encoding, options, personal_dict, file_name=None):
        """Setup the command."""

        cmd = [
            self.binary,
            'list'
        ]

        if encoding:
            cmd.extend(['--encoding', encoding])

        if personal_dict:
            cmd.extend(['--add-extra-dicts', personal_dict])

        disallowed = {
            '?', 'a', 'c', 'v', 'ignore-repl', 'dont-ignore-repl', 'keyboard', 'prefix', 'repl', 'save-repl',
            'dont-save-repl', 'set-prefix', 'dont-set-prefix', 'sug-mode', 'sug-typo-analysis',
            'dont-sug-typo-analysis', 'sug-repl-table', 'dont-sug-repl-table', 'rem-sug-split-char',
            'add-sug-split-char', 'warn', 'affix-compress', 'dont-affix-compress', 'clean-affixes',
            'dont-clean-affixes', 'invisible-soundslike', 'dont-invisible-soundslike', 'partially-expand',
            'dont-partially-expand', 'skip-invalid-words', 'dont-skip-invalid-words', 'validate-affixes',
            'dont-validate-affixes', 'validate-words', 'dont-validate-words', 'b', 'x', 'backup', 'dont-backup',
            'byte-offsets', 'dont-byte-offsets', 'm', 'P', 'guess', 'dont-guess', 'keymapping', 'reverse',
            'dont-reverse', 'suggest', 'dont-suggest', 'time', 'dont-time'

        }

        if 'mode' not in options:
            options['mode'] = 'none'

        for k, v in options.items():
            if k not in disallowed:
                key = ('-%s' if len(k) == 1 else '--%s') % k
                if isinstance(v, bool) and v is True:
                    cmd.append(key)
                elif isinstance(v, str):
                    cmd.extend([key, v])
                elif isinstance(v, int):
                    cmd.extend([key, str(v)])
                elif isinstance(v, list):
                    for value in v:
                        cmd.extend([key, str(value)])

        if file_name is not None:
            cmd.append(file_name)

        return cmd


class Hunspell(SpellChecker):
    """Hunspell spell check class."""

    def __init__(self, config, binary='', verbose=0, default_encoding='', debug=False):
        """Initialize."""

        super().__init__(config, binary, verbose, default_encoding, debug)
        self.binary = binary if binary else 'hunspell'

    @staticmethod
    def get_options(task):
        """Setup spell checker."""

        return task.get('hunspell', {})

    @classmethod
    def setup_dictionary(cls, task, binary, verbose):
        """Setup dictionary."""

        dictionary_options = task.get('dictionary', {})
        output = os.path.abspath(dictionary_options.get('output', os.path.abspath(cls.DICTIONARY)))
        wordlists = dictionary_options.get('wordlists', [])
        if wordlists:
            cls.compile_dictionary(binary, '', dictionary_options.get('wordlists', []), None, output, verbose)
        else:
            output = None
        return output

    @classmethod
    def compile_dictionary(cls, binary, lang, wordlists, encoding, output, verbose):
        """Compile user dictionary."""

        wordlist = ''

        try:
            output_location = os.path.dirname(output)
            if not os.path.exists(output_location):
                os.makedirs(output_location)
            if os.path.exists(output):
                os.remove(output)

            log("Compiling Dictionary...", 1, verbose)
            # Read word lists and create a unique set of words
            words = set()
            for wordlist in wordlists:
                with open(wordlist, 'rb') as src:
                    for word in src.read().split(b'\n'):
                        words.add(word.replace(b'\r', b''))

            # Sort and create wordlist
            with open(output, 'wb') as dest:
                dest.write(b'\n'.join(sorted(words)) + b'\n')
        except Exception:
            log('Problem compiling dictionary.', 0, verbose)
            log("Current wordlist '%s'" % wordlist, verbose)
            raise

    def spell_check_no_pipeline(self, sources, options, personal_dict):
        """Spell check without the pipeline."""

        for source in sources:
            if source._has_error():  # pragma: no cover
                yield Results([], source.context, source.category, source.error)

            cmd = self.setup_command(source.encoding, options, personal_dict, source.context)
            self.log('', 3)
            self.log("Command: " + str(cmd), 4)
            try:
                wordlist = util.call_spellchecker(cmd, input_text=None, encoding=source.encoding)
                yield Results(
                    [w for w in sorted(set(wordlist.replace('\r', '').split('\n'))) if w],
                    source.context,
                    source.category
                )
            except Exception as e:  # pragma: no cover
                err = self.get_error(e)
                yield Results([], source.context, source.category, err)

    def setup_command(self, encoding, options, personal_dict, file_name=None):
        """Setup command."""

        cmd = [
            self.binary,
            '-l'
        ]

        if encoding:
            cmd.extend(['-i', encoding])

        if personal_dict:
            cmd.extend(['-p', personal_dict])

        disallowed = {
            '1', 'a', 'D', 'G', 'h', 'help', 'l', 'L', 'm', 'P', 's', 'S', 'v', 'vv', 'w'
        }

        for k, v in options.items():
            if k not in disallowed:
                key = ('-%s' if len(k) == 1 else '--%s') % k
                if isinstance(v, bool) and v is True:
                    cmd.append(key)
                elif isinstance(v, str):
                    cmd.extend([key, v])
                elif isinstance(v, int):
                    cmd.extend([key, str(v)])
                elif isinstance(v, list):
                    for value in v:
                        cmd.extend([key, str(value)])

        if file_name is not None:
            cmd.append(file_name)

        return cmd


def iter_tasks(matrix, names, groups):
    """Iterate tasks."""

    # Build name index
    name_index = {task.get('name', ''): index for index, task in enumerate(matrix)}

    for index, task in enumerate(matrix):
        name = task.get('name', '')
        group = task.get('group', '')
        hidden = task.get('hidden', False)
        if names and name in names and index == name_index[name]:
            yield task
        elif groups and group in groups and not hidden:
            yield task
        elif not names and not groups and not hidden:
            yield task


class SpellingTask:
    """Process spelling task."""

    GLOB_FLAG_MAP = {
        "CASE": glob.C,
        "C": glob.C,
        "IGNORECASE": glob.I,
        "I": glob.I,
        "RAWCHARS": glob.R,
        "R": glob.R,
        "NEGATE": glob.N,
        "N": glob.N,
        "MINUSNEGATE": glob.M,
        "M": glob.M,
        "GLOBSTAR": glob.G,
        "G": glob.G,
        "DOTGLOB": glob.D,
        "D": glob.D,
        "EXTGLOB": glob.E,
        "E": glob.E,
        "BRACE": glob.B,
        "B": glob.B,
        "FOLLOW": glob.L,
        "L": glob.L,
        "MATCHBASE": glob.X,
        "X": glob.X,
        "NEGATEALL": glob.A,
        "A": glob.A,
        "NOUNIQUE": glob.Q,
        "Q": glob.Q,
        "GLOBTILDE": glob.T,
        "T": glob.T,
        # We will accept these, but we already force them on
        "SPLIT": glob.S,
        "S": glob.S,
        "NODIR": glob.O,
        "O": glob.O
    }

    def __init__(self, checker, config, binary='', verbose=0, jobs=None, debug=False, skip_dict_compile=False):
        """Initialize."""

        if checker == "hunspell":  # pragma: no cover
            spellchecker = Hunspell
        elif checker == "aspell":
            spellchecker = Aspell
        else:
            raise ValueError('%s is not a valid spellchecker!' % checker)

        self.spellchecker = spellchecker
        self.verbose = verbose
        self.config = config
        self.binary = checker if not binary else binary
        self.debug = debug
        self.jobs = jobs
        self.skip_dict_compile = skip_dict_compile

    def log(self, text, level):
        """Log level."""

        log(text, level, verbose=self.verbose)

    def _to_flags(self, text):
        """Convert text representation of flags to actual flags."""

        flags = 0
        for x in text.split('|'):
            value = x.strip().upper()
            if value:
                flags |= self.GLOB_FLAG_MAP.get(value, 0)
        return flags

    def walk_src(self, targets, flags, limit):
        """Walk source and parse files."""

        for target in targets:
            # Glob using `S` for patterns with `|` and `O` to exclude directories.
            kwargs = {"flags": flags | glob.S | glob.O}
            kwargs['limit'] = limit
            yield from glob.iglob(target, **kwargs)

    def get_checker(self):
        """Get a spell checker object."""

        checker = self.spellchecker(
            self.config,
            self.binary,
            self.verbose,
            self.default_encoding,
            self.debug
        )
        checker._build_pipeline(self.task)
        return checker

    def process_file(self, f, checker):
        """Process a given file."""

        self.log('', 2)
        self.log('> Processing: %s' % f, 1)

        source = checker.get_source(f)

        if checker.pipeline_steps is not None:
            yield from checker._spelling_pipeline(source, self.options, self.personal_dict)
        else:
            yield from checker.spell_check_no_pipeline(source, self.options, self.personal_dict)

    def multi_check(self, f):
        """Check the file for spelling errors (for multi-processing)."""

        return list(self.process_file(f, self.get_checker()))

    def run_task(self, task, source_patterns=None):
        """Walk source and initiate spell check."""

        # Perform spell check
        self.log('Running Task: %s...' % task.get('name', ''), 1)

        # Setup filters and variables for the spell check
        self.task = task
        self.default_encoding = self.task.get('default_encoding', '')
        self.options = self.spellchecker.get_options(self.task)
        if not self.skip_dict_compile:
            self.personal_dict = self.spellchecker.setup_dictionary(self.task, self.binary, self.verbose)
        else:
            dictionary_options = self.task.get('dictionary', {})
            output = os.path.abspath(dictionary_options.get('output', os.path.abspath(self.spellchecker.DICTIONARY)))
            if os.path.exists(output):
                self.personal_dict = output
            else:
                self.personal_dict = self.spellchecker.setup_dictionary(self.task, self.binary, self.verbose)
        self.found_match = False
        glob_flags = self._to_flags(self.task.get('glob_flags', "N|B|G"))
        glob_limit = self.task.get('glob_pattern_limit', 1000)

        if not source_patterns:
            source_patterns = self.task.get('sources', [])

        # If jobs was not specified via command line, check the config for jobs settings
        jobs = self.config.get('jobs', 1) if self.jobs is None else self.jobs

        expect_match = self.task.get('expect_match', True)
        if jobs != 1 and jobs > 0:
            # Use multi-processing to process files concurrently
            with ProcessPoolExecutor(max_workers=jobs if jobs else None) as pool:
                for results in pool.map(self.multi_check, self.walk_src(source_patterns, glob_flags, glob_limit)):
                    self.found_match = True
                    yield from results
        else:
            # Avoid overhead of multiprocessing if we are single threaded
            checker = self.get_checker()
            for f in self.walk_src(source_patterns, glob_flags, glob_limit):
                self.found_match = True
                yield from self.process_file(f, checker)

        if not self.found_match and expect_match:
            raise RuntimeError(
                'None of the source targets from the configuration match any files:\n{}'.format(
                    '\n'.join(f'- {target}' for target in source_patterns)
                )
            )


def spellcheck(
    config_file,
    names=None,
    groups=None,
    binary='',
    checker='',
    sources=None,
    verbose=0,
    debug=False,
    jobs=None,
    skip_dict_compile=False
):
    """Spell check."""

    config = util.read_config(config_file)
    if sources is None:
        sources = []

    matrix = config.get('matrix')
    preferred_checker = config.get('spellchecker', 'aspell')

    if matrix is None:
        matrix = config.get('documents')
        if matrix is not None:
            util.warn_deprecated("'documents' key in config is deprecated. 'matrix' should be used going forward.")
        else:
            raise KeyError(
                'Unable to find or load matrix from pyspelling'
                ' configuration, for more'
                ' details on configuration please read'
                ' https://facelessuser.github.io/pyspelling/configuration/'
            )

    groups = set() if groups is None else set(groups)
    names = set() if names is None else set(names)

    # Sources are only recognized when requesting a single name.
    if (len(names) != 1 and len(sources)):
        sources = []

    processed_tasks = 0

    for task in iter_tasks(matrix, names, groups):

        processed_tasks += 1

        if not checker:
            checker = preferred_checker

        log('Using {} to spellcheck {}'.format(checker, task.get('name', '')), 1, verbose)

        spelltask = SpellingTask(checker, config, binary, verbose, jobs, debug, skip_dict_compile)

        for result in spelltask.run_task(task, source_patterns=sources):
            log('Context: %s' % result.context, 2, verbose)
            yield result

        log("", 1, verbose)

    if processed_tasks == 0:
        raise ValueError(
            'There are either no tasks in the configuration file'
            ' or the specified name or group can not be found.'
        )
