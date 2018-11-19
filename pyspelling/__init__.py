"""Spell check with Aspell or Hunspell."""
from __future__ import unicode_literals
import os
import importlib
from . import util
from .__meta__ import __version__, __version_info__  # noqa: F401
from . import flow_control
from . import filters
from wcmatch import glob
import codecs
from collections import namedtuple

__all__ = ("spellcheck",)


class Results(namedtuple('Results', ['words', 'context', 'category', 'error'])):
    """Results."""

    def __new__(cls, words, context, category, error=None):
        """Allow defaults."""

        return super().__new__(cls, words, context, category, error)


class SpellChecker:
    """Spell check class."""

    DICTIONARY = 'dictionary.dic'

    GLOB_FLAG_MAP = {
        "FORECECASE": glob.F,
        "F": glob.F,
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
        "B": glob.B
    }

    def __init__(self, config, binary='', verbose=0, debug=False):
        """Initialize."""

        # General options
        self.binary = binary if binary else 'aspell'
        self.verbose = verbose
        self.dict_bin = os.path.abspath(self.DICTIONARY)
        self.debug = debug
        self.default_encoding = ''

    def log(self, text, level):
        """Log level."""
        if self.verbose >= level:
            print(text)

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

    def compile_dictionary(self, lang, wordlists, output):
        """Compile user dictionary."""

    def _walk_src(self, targets, flags, pipeline):
        """Walk source and parse files."""

        for target in targets:
            patterns = glob.globsplit(target, flags=flags)
            for f in glob.iglob(patterns, flags=flags):
                if not os.path.isdir(f):
                    self.log('', 2)
                    self.log('> Processing: %s' % f, 1)
                    if pipeline:
                        try:
                            yield pipeline[0]._run_first(f)
                        except Exception as e:
                            err = self.get_error(e)
                            yield [filters.SourceText('', f, '', '', err)]
                    else:
                        try:
                            if self.default_encoding:
                                encoding = filters.PYTHON_ENCODING_NAMES.get(
                                    self.default_encoding, self.default_encoding
                                ).lower()
                                encoding = codecs.lookup(encoding).name
                            else:
                                encoding = self.default_encoding
                            yield [filters.SourceText('', f, encoding, 'file')]
                        except Exception as e:
                            err = self.get_error(e)
                            yield [filters.SourceText('', f, '', '', err)]

    def setup_spellchecker(self, task):
        """Setup spell checker."""

        return {}

    def setup_dictionary(self, task):
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
                    name, options = list(step.items())[0]
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

    def _to_flags(self, text):
        """Convert text representation of flags to actual flags."""

        flags = 0
        for x in text.split('|'):
            value = x.strip().upper()
            if value:
                flags |= self.GLOB_FLAG_MAP.get(value, 0)
        return flags

    def run_task(self, task, source_patterns=None):
        """Walk source and initiate spell check."""

        # Perform spell check
        self.log('Running Task: %s...' % task.get('name', ''), 1)

        # Setup filters and variables for the spell check
        self.default_encoding = task.get('default_encoding', '')
        options = self.setup_spellchecker(task)
        personal_dict = self.setup_dictionary(task)
        glob_flags = self._to_flags(task.get('glob_flags', "N|B|G"))
        self._build_pipeline(task)

        if not source_patterns:
            source_patterns = task.get('sources', [])

        for sources in self._walk_src(source_patterns, glob_flags, self.pipeline_steps):

            if self.pipeline_steps is not None:
                yield from self._spelling_pipeline(sources, options, personal_dict)
            else:
                yield from self.spell_check_no_pipeline(sources, options, personal_dict)


class Aspell(SpellChecker):
    """Aspell spell check class."""

    def __init__(self, config, binary='', verbose=0, debug=False):
        """Initialize."""

        super().__init__(config, binary, verbose, debug)
        self.binary = binary if binary else 'aspell'

    def setup_spellchecker(self, task):
        """Setup spell checker."""

        return task.get('aspell', {})

    def setup_dictionary(self, task):
        """Setup dictionary."""

        dictionary_options = task.get('dictionary', {})
        output = os.path.abspath(dictionary_options.get('output', self.dict_bin))
        aspell_options = task.get('aspell', {})
        lang = aspell_options.get('lang', aspell_options.get('l', 'en'))
        wordlists = dictionary_options.get('wordlists', [])
        if lang and wordlists:
            self.compile_dictionary(
                lang,
                dictionary_options.get('wordlists', []),
                dictionary_options.get('encoding', 'utf-8'),
                output
            )
        else:
            output = None
        return output

    def compile_dictionary(self, lang, wordlists, encoding, output):
        """Compile user dictionary."""

        cmd = [
            self.binary,
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

            self.log("Compiling Dictionary...", 1)
            # Read word lists and create a unique set of words
            words = set()
            for wordlist in wordlists:
                with open(wordlist, 'rb') as src:
                    for word in src.read().split(b'\n'):
                        words.add(word.replace(b'\r', b''))

            # Compile wordlist against language
            util.call(
                [
                    self.binary,
                    '--lang', lang,
                    '--encoding=utf-8',
                    'create',
                    'master', output
                ],
                input_text=b'\n'.join(sorted(words)) + b'\n'
            )
        except Exception:
            self.log(cmd, 0)
            self.log("Current wordlist: '%s'" % wordlist, 0)
            self.log("Problem compiling dictionary. Check the binary path and options.", 0)
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

        allowed = {
            'conf-dir', 'data-dir', 'add-dict-alias', 'rem-dict-alias', 'dict-dir',
            'encoding', 'add-filter', 'rem-filter', 'add-filter-path', 'rem-filter-path',
            'mode', 'e', 'H', 't', 'n', 'add-extra-dicts', 'rem-extra-dicts', 'home-dir',
            'ingore', 'W', 'dont-ignore-case', 'ignore-case', 'lang', 'l', 'local-data-dir',
            'd', 'master', 'dont-normalize', 'normalize', 'dont-norm-required',
            'norm-required', 'norm-form', 'dont-norm-strict', 'norm-strict', 'per-conf',
            'p', 'personal', 'C', 'B', 'dont-run-together', 'run-together', 'run-together-limit',
            'run-together-min', 'use-other-dicts', 'dont-use-other-dicts', 'add-variety', 'rem-variety',
            'add-context-delimiters', 'rem-context-delimiters', 'dont-context-visible-first',
            'context-visible-first', 'add-email-quote', 'rem-email-quote', 'email-margin',
            'add-html-check', 'rem-html-check', 'add-html-skip', 'rem-html-skip', 'add-sgml-check',
            'rem-sgml-check', 'add-sgml-skip', 'rem-sgml-skip', 'dont-tex-check-comments',
            'tex-check-comments', 'add-tex-command', 'rem-tex-command', 'add-texinfo-ignore',
            'rem-texinfo-ignore', 'add-texinfo-ignore-env', 'rem-texinfo-ignore-env', 'filter'
        }

        for k, v in options.items():
            if k in allowed:
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

    def __init__(self, config, binary='', verbose=0, debug=False):
        """Initialize."""

        super().__init__(config, binary, verbose, debug)
        self.binary = binary if binary else 'hunspell'

    def setup_spellchecker(self, task):
        """Setup spell checker."""

        return task.get('hunspell', {})

    def setup_dictionary(self, task):
        """Setup dictionary."""

        dictionary_options = task.get('dictionary', {})
        output = os.path.abspath(dictionary_options.get('output', self.dict_bin))
        lang = dictionary_options.get('lang', 'en_US')
        wordlists = dictionary_options.get('wordlists', [])
        if lang and wordlists:
            self.compile_dictionary(lang, dictionary_options.get('wordlists', []), None, output)
        else:
            output = None
        return output

    def compile_dictionary(self, lang, wordlists, encoding, output):
        """Compile user dictionary."""
        wordlist = ''

        try:
            output_location = os.path.dirname(output)
            if not os.path.exists(output_location):
                os.makedirs(output_location)
            if os.path.exists(output):
                os.remove(output)

            self.log("Compiling Dictionary...", 1)
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
            self.log('Problem compiling dictionary.', 0)
            self.log("Current wordlist '%s'" % wordlist)
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

        allowed = {
            'check-apostrophe', 'check-url',
            'd', 'H', 'i', 'n', 'O', 'r', 't', 'X'
        }

        for k, v in options.items():
            if k in allowed:
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
    name_index = dict([(task.get('name', ''), index) for index, task in enumerate(matrix)])

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


def spellcheck(config_file, names=None, groups=None, binary='', checker='', sources=None, verbose=0, debug=False):
    """Spell check."""

    hunspell = None
    aspell = None
    spellchecker = None
    config = util.read_config(config_file)
    if sources is None:
        sources = []

    matrix = config.get('matrix', [])
    preferred_checker = config.get('spellchecker', 'aspell')
    if not matrix:
        matrix = config.get('documents', [])
        if matrix:
            util.warn_deprecated("'documents' key in config is deprecated. 'matrix' should be used going forward.")

    groups = set() if groups is None else set(groups)
    names = set() if names is None else set(names)

    # Sources are only recognized when requesting a single name.
    if (len(names) != 1 and len(sources)):
        sources = []

    for task in iter_tasks(matrix, names, groups):

        if not checker:
            checker = preferred_checker

        if checker == "hunspell":  # pragma: no cover
            if hunspell is None:
                hunspell = Hunspell(config, binary, verbose, debug)
            spellchecker = hunspell

        elif checker == "aspell":
            if aspell is None:
                aspell = Aspell(config, binary, verbose, debug)
            spellchecker = aspell
        else:
            raise ValueError('%s is not a valid spellchecker!' % checker)

        spellchecker.log('Using %s to spellcheck %s' % (checker, task.get('name', '')), 1)
        for result in spellchecker.run_task(task, source_patterns=sources):
            spellchecker.log('Context: %s' % result.context, 2)
            yield result
        spellchecker.log("", 1)
