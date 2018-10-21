"""Spell check with Aspell or Hunspell."""
from __future__ import unicode_literals
import os
import importlib
from . import util
from . import __meta__
from . import settings
from . import flow_control
from . import filters
from wcmatch import glob

__version__ = __meta__.version
__version_info__ = __meta__.version_info

__all__ = ("__version__", "__version_info__", "spellcheck")


class SpellChecker(object):
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

    def log(self, text, level):
        """Log level."""
        if self.verbose >= level:
            print(text)

    def get_error(self, e):
        """Get the error."""

        import traceback

        return traceback.format_exc() if self.debug else str(e)

    def setup_command(self, encoding, options, personal_dict):
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
                        status = f.adjust_flow(source.category)
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
                            srcs = f.sfilter(source)
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
            if source._has_error():
                yield util.Results([], source.context, source.category, source.error)
            else:
                encoding = source.encoding
                if source._is_bytes():
                    text = source.text
                else:
                    text = source.text.encode(encoding)
                self.log('', 3)
                self.log(text, 3)
                cmd = self.setup_command(encoding, options, personal_dict)
                self.log("Command: " + str(cmd), 4)

                wordlist = util.call_spellchecker(cmd, input_text=text, encoding=encoding)
                yield util.Results([w for w in sorted(set(wordlist.split('\n'))) if w], source.context, source.category)

    def compile_dictionary(self, lang, wordlists, output):
        """Compile user dictionary."""

    def _walk_src(self, targets, flags, plugin):
        """Walk source and parse files."""

        for target in targets:
            patterns = glob.globsplit(target, flags=flags)
            for f in glob.iglob(patterns, flags=flags):
                if not os.path.isdir(f):
                    self.log('', 2)
                    self.log('> Processing: %s' % f, 1)
                    try:
                        yield plugin._parse(f)
                    except Exception as e:
                        err = self.get_error(e)
                        yield filters.SourceText('', f, '', '', err)

    def setup_spellchecker(self, task):
        """Setup spell checker."""

        return {}

    def setup_dictionary(self, task):
        """Setup dictionary."""

        return None

    def _build_pipeline(self, task, default_encoding):
        """Build up the pipeline."""

        self.pipeline_steps = []
        kwargs = {}
        if default_encoding:
            kwargs["default_encoding"] = default_encoding

        steps = task.get('pipeline', [])
        if not steps:
            steps = task.get('filters', [])
            util.warn_deprecated("'filters' key in config is deprecated. 'pipeline' should be used going forward.")

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

    def run_task(self, task):
        """Walk source and initiate spell check."""

        # Perform spell check
        self.log('Running Task: %s...' % task.get('name', ''), 1)

        # Setup filters and variables for the spell check
        encoding = task.get('default_encoding', '')
        options = self.setup_spellchecker(task)
        output = self.setup_dictionary(task)
        glob_flags = self._to_flags(task.get('glob_flags', "N|B|G"))
        self._build_pipeline(task, encoding)

        for sources in self._walk_src(task.get('sources', []), glob_flags, self.pipeline_steps[0]):
            yield from self._spelling_pipeline(sources, options, output)


class Aspell(SpellChecker):
    """Aspell spell check class."""

    def __init__(self, config, binary='', verbose=0, debug=False):
        """Initialize."""

        super(Aspell, self).__init__(config, binary, verbose, debug)
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
            self.compile_dictionary(lang, dictionary_options.get('wordlists', []), output)
        else:
            output = None
        return output

    def compile_dictionary(self, lang, wordlists, output):
        """Compile user dictionary."""

        cmd = [
            self.binary,
            '--lang', lang,
            '--encoding=utf-8',
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

    def setup_command(self, encoding, options, personal_dict):
        """Setup the command."""

        cmd = [
            self.binary,
            'list',
            '--encoding', encoding
        ]

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
        return cmd


class Hunspell(SpellChecker):
    """Hunspell spell check class."""

    def __init__(self, config, binary='', verbose=0, debug=False):
        """Initialize."""

        super(Hunspell, self).__init__(config, binary, verbose)
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
            self.compile_dictionary(lang, dictionary_options.get('wordlists', []), output)
        else:
            output = None
        return output

    def compile_dictionary(self, lang, wordlists, output):
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

    def setup_command(self, encoding, options, personal_dict):
        """Setup command."""

        cmd = [
            self.binary,
            '-l',
            '-i', encoding
        ]

        if personal_dict:
            cmd.extend(['-p', personal_dict])

        allowed = {
            'check-apostrophe', 'check-url',
            'd', 'H', 'n', 'o', 'r', 't', 'X'
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
        return cmd


def spellcheck(config_file, name='', binary='', verbose=0, checker='', debug=False):
    """Spell check."""

    hunspell = None
    aspell = None
    spellchecker = None
    config = settings.read_config(config_file)

    matrix = config.get('matrix', [])
    preferred_checker = config.get('spellchecker', 'aspell')
    if not matrix:
        matrix = config.get('documents', [])
        if matrix:
            util.warn_deprecated("'documents' key in config is deprecated. 'matrix' should be used going forward.")

    for task in matrix:

        if name and name != task.get('name', ''):
            continue

        if not checker:
            checker = preferred_checker

        if checker == "hunspell":
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
        for result in spellchecker.run_task(task):
            spellchecker.log('Context: %s' % result.context, 2)
            yield result
        spellchecker.log("", 1)
