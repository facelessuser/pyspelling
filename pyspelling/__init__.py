"""Spell check with Aspell or Hunspell."""
from __future__ import unicode_literals
import os
import fnmatch
import re
import importlib
from . import util
from . import parsers


class Spelling(object):
    """Spell check class."""

    DICTIONARY = 'dictionary.dic'

    def __init__(self, config, verbose=False):
        """Initialize."""

        # General options
        self.verbose = verbose
        self.dict_bin = os.path.abspath(self.DICTIONARY)
        self.documents = config.get('documents', [])
        self.dictionary = config.get('dictionary', [])

    def normalize_utf(self, encoding):
        """Normalize UTF encoding."""

        if encoding == 'utf-8-sig':
            encoding = 'utf-8'
        if encoding.startswith('utf-16'):
            encoding = 'utf-16'
        elif encoding.startswith('utf-32'):
            encoding = 'utf-32'
        return encoding

    def check_spelling(self, sources, options, personal_dict):
        """Check spelling."""

        fail = False

        for source in sources:
            if source.encoding == 'bin':
                print('ERROR: Could not read %s' % source.context)
                continue
            if self.verbose:
                print('CHECK: %s' % source.context)

            text = source.text
            if isinstance(source, parsers.SourceText):
                for f, disallow in self.filters:
                    if source.type not in disallow:
                        text = f.filter(text)
                print(text)
                text = text.encode(source.encoding)

            if self.spellchecker == 'hunspell':
                cmd = [
                    'hunspell',
                    '-l',
                    '-i', self.normalize_utf(source.encoding),
                ]

                if personal_dict:
                    cmd.extend(['-p', personal_dict])

                allowed = {
                    'check-apostrophe', 'check-url',
                    'i', 'd' 'H', 'n', 'o', 'r', 't', 'X'
                }

            else:
                cmd = [
                    'aspell',
                    'list',
                    '--encoding', self.normalize_utf(source.encoding)
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
                    elif isinstance(v, util.ustr):
                        cmd.extend([key, v])
                    elif isinstance(v, int):
                        cmd.extend([key, util.ustr(v)])
                    elif isinstance(v, list):
                        for value in v:
                            cmd.extend([key, util.ustr(value)])

            wordlist = util.console(cmd, input_text=text)
            words = [w for w in sorted(set(wordlist.split('\n'))) if w]

            if words:
                fail = True
                print('Misspelled words:\n<%s> %s' % (source.type, source.context))
                print('-' * 80)
                for word in words:
                    print(word)
                print('-' * 80)
                print('')
        return fail

    def compile_dictionary(self, lang, wordlists, output):
        """Compile user dictionary."""

        output_location = os.path.dirname(output)
        if not os.path.exists(output_location):
            os.makedirs(output_location)
        if os.path.exists(output):
            os.remove(output)

        print("Compiling Dictionary...")
        # Read word lists and create a unique set of words
        words = set()
        for wordlist in wordlists:
            with open(wordlist, 'rb') as src:
                for word in src.read().split(b'\n'):
                    words.add(word.replace(b'\r', b''))

        if self.spellchecker == 'hunspell':
            # Sort and create wordlist
            with open(self.dict_bin, 'wb') as dest:
                dest.write(b'\n'.join(sorted(words)) + b'\n')
        else:
            # Compile wordlist against language
            util.console(
                [
                    'aspell',
                    '--lang', lang,
                    '--encoding=utf-8',
                    'create',
                    'master', output
                ],
                input_text=b'\n'.join(sorted(words)) + b'\n'
            )

    def skip_target(self, target):
        """Check if target should be skipped."""

        return self.skip_wild_card_target(target) or self.skip_regex_target(target)

    def skip_wild_card_target(self, target):
        """Check if target should be skipped via wildcard patterns."""

        exclude = False
        for pattern in self.excludes:
            if fnmatch.fnmatch(target, pattern):
                exclude = True
                break
        return exclude

    def skip_regex_target(self, target):
        """Check if target should be skipped via regex."""

        exclude = False
        for pattern in self.regex_excludes:
            if pattern.match(target, pattern):
                exclude = True
                break
        return exclude

    def is_valid_file(self, file_name, file_patterns):
        """Is file in current file patterns."""

        okay = False
        lowered = file_name.lower()
        for pattern in file_patterns:
            if fnmatch.fnmatch(lowered, pattern):
                okay = True
                break
        return okay

    def walk_src(self, targets, plugin):
        """Walk source and parse files."""

        # Override file_patterns if the user provides their own
        file_patterns = self.file_patterns if self.file_patterns else plugin.FILE_PATTERNS
        for target in targets:
            if not os.path.exists(target):
                continue
            if os.path.isdir(target):
                if self.skip_target(target):
                    continue
                for base, dirs, files in os.walk(target):
                    [dirs.remove(d) for d in dirs[:] if self.skip_target(os.path.join(base, d))]
                    for f in files:
                        file_path = os.path.join(base, f)
                        if self.skip_target(file_path):
                            continue
                        if self.is_valid_file(f, file_patterns):
                            yield plugin.parse_file(file_path)
            elif self.is_valid_file(target, file_patterns):
                if self.skip_target(target):
                    continue
                yield plugin.parse_file(target)

    def setup_spellchecker(self, documents):
        """Setup spell checker."""

        self.spellchecker = documents.get('spell_checker', 'aspell')
        if self.spellchecker == 'hunspell':
            options = documents.get('hunspell', {})
        else:
            options = documents.get('aspell', {})

        return options

    def setup_dictionary(self, documents):
        """Setup dictionary."""

        dictionary_options = documents.get('dictionary', {})
        output = os.path.abspath(dictionary_options.get('output', self.dict_bin))
        lang = dictionary_options.get('lang', 'en' if self.spellchecker == 'aspell' else 'en_US')
        wordlists = dictionary_options.get('wordlists', [])
        if lang and wordlists:
            self.compile_dictionary(lang, dictionary_options.get('wordlists', []), output)
        else:
            output = None
        return output

    def setup_excludes(self, documents):
        """Setup excludes."""

        # Read excludes
        self.excludes = documents.get('excludes', [])
        self.regex_excludes = [re.compile(exclude) for exclude in documents.get('regex_excludes', [])]

    def get_filters(self, documents):
        """Get filters."""
        self.filters = []
        for f in documents.get('filters', []):
            # Retrieve module and module options
            if isinstance(f, dict):
                name, options = list(f.items())[0]
            else:
                name = f
                options = {}
            if options is None:
                options = {}

            # Extract disallowed tokens
            disallow = tuple()
            if 'disallow' in options:
                disallow = options['disallow']
                del options['disallow']

            self.filters.append((self.get_module(name, 'get_filter')(options), disallow))

    def get_module(self, module, accessor):
        """Get module."""

        if isinstance(module, util.string_type):
            mod = importlib.import_module(module)
        attr = getattr(mod, accessor, None)
        if not attr:
            raise ValueError("Could not find accessor '%s'!" % accessor)
        return attr()

    def check(self):
        """Walk source and initiate spell check."""

        fail = False
        for documents in self.documents:
            print('')
            # Setup parser and variables for the spell check
            parser = self.get_module(documents['parser'], 'get_parser')(
                documents.get('options', {}), documents.get('fallback_encoding', 'ascii')
            )
            self.file_patterns = documents.get('file_patterns', [])

            options = self.setup_spellchecker(documents)
            output = self.setup_dictionary(documents)
            self.get_filters(documents)
            self.setup_excludes(documents)

            # Perform spell check
            print('Spell Checking %s...' % documents.get('name', ''))
            for sources in self.walk_src(documents.get('src', []), parser):
                if self.check_spelling(sources, options, output):
                    fail = True
        return fail
