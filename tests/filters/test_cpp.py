"""Test CPP plugin."""
from .. import util


class TestCPP(util.PluginTestCase):
    """Test CPP plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: cpp
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.cpp:
                  group_comments: true
                  trigraphs: true
            """
        ).format(self.tempdir)
        self.mktemp('.cpp.yml', config, 'utf-8')

    def test_cpp(self):
        """Test CPP."""

        bad_block = ['helo', 'begn']
        bad_comments = ['flga', 'graet']
        bad_comments2 = ['recieve', 'teh']
        bad_comments3 = ['hpoe', 'lvoe']
        bad_words = bad_block + bad_comments + bad_comments2 + bad_comments3
        good_words = ['yes', 'word']
        template = self.dedent(
            """
            /*
            {}
            */
            uint8_t func() {{
                uint8_t tsdd = 3;
                // {}
                // {} \
                reurn tsdd;

                uint32_t trigraph_test = (CONSTANT_1 ??' ADKASLD) ??' CONSTANT_2; // {}

                rtuern ddst;
            }}
            """
        ).format(
            '\n'.join(bad_block + good_words),
            ' '.join(bad_comments + good_words),
            ' '.join(bad_comments2 + good_words),
            ' '.join(bad_comments3 + good_words)
        )

        # Capture comment continuation
        bad_words.extend(['reurn', 'tsdd'])
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.cpp.yml', bad_words)


class TestCPPGroupedComments(util.PluginTestCase):
    """Test CPP plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: cpp
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.cpp:
                  group_comments: true
                  trigraphs: true
              - pyspelling.filters.context:
                  context_visible_first: true
                  escapes: '\\[\\`]'
                  delimiters:
                  # Ignore multiline content between fences (fences can have 3 or more back ticks)
                  # ```
                  # content
                  # ```
                  - open: '(?s)^(?P<open> *`{{3,}})$'
                    close: '^(?P=open)$'
                  # Ignore text between inline back ticks
                  - open: '(?P<open>`+)'
                    close: '(?P=open)'
            """
        ).format(self.tempdir)
        self.mktemp('.cpp.yml', config, 'utf-8')

    def test_cpp_grouped_comments(self):
        """Test CPP."""

        template = self.dedent(
            """
            uint8_t func() {

              uint32_t test = 3; // what
              // bbbb

              // ```
              // akdjal dlkajdlf dkkjkj
              // skjdl djkjf lslsl
              // ```

              // aaaa
            }
            """
        )
        bad_words = ['aaaa', 'bbbb']
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.cpp.yml', bad_words)


class TestCPPStringAllow(util.PluginTestCase):
    """Test CPP allow filter."""

    def setup_fs(self):
        """Setup."""

        template = self.dedent(
            r"""
            uint8_t func() {
                auto s0 =   "aaaa"; // char
                auto s1 =  L"bbbb"; // wchar_t
                auto s2 = u8"cccc"; // char
                auto s3 =  u"dddd"; // char16_t
                auto s4 =  U"eeee"; // char32_t
                auto R0 =   R"("ffff")"; // const char*
                auto R1 =   R"delim("gggg")delim";    // const char*
                auto R3 =  LR"("hhhh")"; // const wchar_t*
                auto R4 = u8R"("iiii")"; // const char*, encoded as UTF-8
                auto R5 =  uR"("jjjj")"; // const char16_t*, encoded as UTF-16
                auto R6 =  UR"("kkkk")"; // const char32_t*, encoded as UTF-32
            }
            """
        )

        self.mktemp('test.txt', template, 'utf-8')

    def test_exclude_raw(self):
        """Test raw exclusion."""

        config = self.dedent(
            """
            matrix:
            - name: cpp
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.cpp:
                  strings: true
                  line_comments: false
                  group_comments: true
                  string_types: uls
            """
        ).format(self.tempdir)
        self.mktemp('.cpp.yml', config, 'utf-8')
        self.assert_spellcheck('.cpp.yml', ['aaaa', 'bbbb', 'cccc', 'dddd', 'eeee'])

    def test_exclude_unicode(self):
        """Test Unicode exclusion."""

        config = self.dedent(
            """
            matrix:
            - name: cpp
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.cpp:
                  strings: true
                  line_comments: false
                  group_comments: true
                  string_types: rls
            """
        ).format(self.tempdir)
        self.mktemp('.cpp.yml', config, 'utf-8')
        self.assert_spellcheck('.cpp.yml', ["aaaa", "bbbb", "ffff", "gggg", "hhhh"])

    def test_exclude_wide(self):
        """Test wide exclusion."""

        config = self.dedent(
            """
            matrix:
            - name: cpp
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.cpp:
                  strings: true
                  line_comments: false
                  group_comments: true
                  string_types: rus
            """
        ).format(self.tempdir)
        self.mktemp('.cpp.yml', config, 'utf-8')
        self.assert_spellcheck('.cpp.yml', ["aaaa", "cccc", "dddd", "eeee", "ffff", "gggg", "iiii", "jjjj", "kkkk"])

    def test_exclude_standard(self):
        """Test standard exclusion."""

        config = self.dedent(
            """
            matrix:
            - name: cpp
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.cpp:
                  strings: true
                  line_comments: false
                  group_comments: true
                  string_types: rul
            """
        ).format(self.tempdir)
        self.mktemp('.cpp.yml', config, 'utf-8')
        self.assert_spellcheck('.cpp.yml', ["bbbb", "cccc", "dddd", "eeee", "hhhh", "iiii", "jjjj", "kkkk"])

    def test_include_all(self):
        """Test standard exclusion."""

        config = self.dedent(
            """
            matrix:
            - name: cpp
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.cpp:
                  strings: true
                  line_comments: false
                  group_comments: true
                  string_types: '*'
            """
        ).format(self.tempdir)
        self.mktemp('.cpp.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.cpp.yml',
            ["aaaa", "bbbb", "cccc", "dddd", "eeee", "ffff", "gggg", "hhhh", "iiii", "jjjj", "kkkk"]
        )

    def test_include_all_raw(self):
        """Test standard exclusion."""

        config = self.dedent(
            """
            matrix:
            - name: cpp
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.cpp:
                  strings: true
                  line_comments: false
                  group_comments: true
                  string_types: 'r*'
            """
        ).format(self.tempdir)
        self.mktemp('.cpp.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.cpp.yml',
            ["ffff", "gggg", "hhhh", "iiii", "jjjj", "kkkk"]
        )

    def test_include_all_unicode(self):
        """Test standard exclusion."""

        config = self.dedent(
            """
            matrix:
            - name: cpp
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.cpp:
                  strings: true
                  line_comments: false
                  group_comments: true
                  string_types: 'u*'
            """
        ).format(self.tempdir)
        self.mktemp('.cpp.yml', config, 'utf-8')
        self.assert_spellcheck(
            '.cpp.yml',
            ["cccc", "dddd", "eeee", "iiii", "jjjj", "kkkk"]
        )


class TestCPPStrings(util.PluginTestCase):
    """Test CPP plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: cpp
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.cpp:
                  strings: true
                  line_comments: false
                  group_comments: true
                  string_types: ruls
            """
        ).format(self.tempdir)
        self.mktemp('.cpp.yml', config, 'utf-8')

    def test_cpp_strings(self):
        """Test CPP strings."""

        bad_char = ['helo', 'begn']
        bad_wchar = ['flga', 'graet']
        bad_u8 = ['recieve', 'teh']
        bad_u16 = ['acept', 'thruogh']
        bad_u32 = ['hpoe', 'lvoe']
        bad_raw = ['aaaa', 'bbbb']
        bad_raw_delim = ['cccc', 'dddd']
        bad_raw_wide = ['eeee', 'ffff']
        bad_raw_u8 = ['gggg', 'hhhh']
        bad_raw_u16 = ['iiii', 'jjjj']
        bad_raw_u32 = ['kkkk', 'llll']

        bad_words = (
            bad_char + bad_wchar + bad_u8 + bad_u16 + bad_u32 + bad_raw + bad_raw_wide +
            bad_raw_delim + bad_raw_u8 + bad_raw_u16 + bad_raw_u32
        )
        good_words = ['yes', 'word']
        template = self.dedent(
            r"""
            uint8_t func() {{
                auto c0 =   'xxxx'; // char
                auto s0 =   "{}"; // char
                auto s1 =  L"{}"; // wchar_t
                auto s2 = u8"{}"; // char
                auto s3 =  u"{}"; // char16_t
                auto s4 =  U"{}"; // char32_t
                auto R0 =   R"("{}")"; // const char*
                auto R1 =   R"delim("{}")delim";    // const char*
                auto R3 =  LR"("{}")"; // const wchar_t*
                auto R4 = u8R"("{}")"; // const char*, encoded as UTF-8
                auto R5 =  uR"("{}")"; // const char16_t*, encoded as UTF-16
                auto R6 =  UR"("{}")"; // const char32_t*, encoded as UTF-32
            }}
            """
        ).format(
            ' '.join(bad_char + good_words),
            ' '.join(bad_wchar + good_words),
            ' '.join(bad_u8 + good_words),
            ' '.join(bad_u16 + good_words),
            ' '.join(bad_u32 + good_words),
            ' '.join(bad_raw + good_words),
            ' '.join(bad_raw_delim + good_words),
            ' '.join(bad_raw_wide + good_words),
            ' '.join(bad_raw_u8 + good_words),
            ' '.join(bad_raw_u16 + good_words),
            ' '.join(bad_raw_u32 + good_words)
        )

        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.cpp.yml', bad_words)

    def test_cpp_strings_escapes(self):
        """Test CPP strings escapes."""

        template = self.dedent(
            r"""
            uint8_t func() {{
                auto s0 =   "\x61gggg\141 \ntext\
                             \u0061yyyy \\ubbbb"; // char
                auto s1 =  L"\x0061hhhh \ntexts"; // wchar_t
                auto s2 = u8"\141\x000000061\u0061\U00000061"; // char
                auto s3 =  u"\142\x000000062\u0062\U00000062"; // char16_t
                auto s4 =  U"\143\x000000063\u0063\U00000063"; // char32_t
                auto R0 =   R"("\xaa \nbad")"; // const char*
                auto R1 =   R"delim("\xbb
                                     \vbad")delim";    // const char*
                auto R3 =  LR"("\xcc")"; // const wchar_t*
                auto R4 = u8R"("\xdd")"; // const char*, encoded as UTF-8
                auto R5 =  uR"("\xee")"; // const char16_t*, encoded as UTF-16
                auto R6 =  UR"("\xff")"; // const char32_t*, encoded as UTF-32
            }}
            """
        )

        # `char*` and `wchar*` will have escapes `\x`, `\u`, and `\U` stripped out as we don't know the encoding.
        # Unicode strings will have all escapes decoded.
        # Raw will decode none.
        bad_words = [
            'agggga', 'ahhhh', 'ayyyy', 'aaaa', 'bbbb', 'cccc',
            'xaa', 'xbb', 'xcc', 'xdd', 'xee', 'xff',
            'ubbbb', 'nbad', 'vbad'
        ]

        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.cpp.yml', bad_words)


class TestCPPGeneric(util.PluginTestCase):
    """Test CPP plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: cpp
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.cpp:
                  group_comments: true
                  generic_mode: true
            """
        ).format(self.tempdir)
        self.mktemp('.cpp.yml', config, 'utf-8')

    def test_cpp(self):
        """Test CPP."""

        bad_block = ['helo', 'begn']
        bad_comments = ['flga', 'graet']
        bad_comments2 = ['recieve', 'teh']
        bad_words = bad_block + bad_comments + bad_comments2
        good_words = ['yes', 'word']
        template = self.dedent(
            r"""
            /*
            {}
            */
            uint8_t func() {{
                uint8_t tsdd = 3;
                // {}
                // {} \
                reurn tsdd;

                rtuern ddst;
            }}
            """
        ).format(
            '\n'.join(bad_block + good_words),
            ' '.join(bad_comments + good_words),
            ' '.join(bad_comments2 + good_words)
        )

        # Capture comment continuation
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.cpp.yml', bad_words)


class TestCPPChained(util.PluginTestCase):
    """Test chained CPP plugin."""

    def setup_fs(self):
        """Setup file system."""

        config = self.dedent(
            """
            matrix:
            - name: cpp
              sources:
              - '{}/**/*.txt'
              aspell:
                lang: en
              hunspell:
                d: en_US
              pipeline:
              - pyspelling.filters.text:
              - pyspelling.filters.cpp:
                  group_comments: true
            """
        ).format(self.tempdir)
        self.mktemp('.cpp.yml', config, 'utf-8')

    def test_cpp_after_text(self):
        """Test cpp after text."""

        bad_block = ['helo', 'begn']
        bad_comments = ['flga', 'graet']
        bad_comments2 = ['recieve', 'teh']
        bad_words = bad_block + bad_comments + bad_comments2
        good_words = ['yes', 'word']
        template = self.dedent(
            """
            /*
            {}
            */
            uint8_t func() {{
                uint8_t tsdd = 3;
                // {}
                // {}
                reurn tsdd;
            }}
            """
        ).format(
            '\n'.join(bad_block + good_words),
            ' '.join(bad_comments + good_words),
            ' '.join(bad_comments2 + good_words)
        )
        self.mktemp('test.txt', template, 'utf-8')
        self.assert_spellcheck('.cpp.yml', bad_words)
