"""Contains the RequireSnippet class."""
import re
from .utils import get_pref, get_project_pref, get_quotes, should_add_semicolon
from .utils import get_jscs_options, strip_snippet_groups
import sublime

quote_block = '("([^"]+)"|\'([^\']+)\')'
CONTAINS_IMPORT = '^\s*import\s.*\sfrom\s+%s' % quote_block
CONTAINS_REQUIRE = '.+?require\s*\(\s*%s\s*\)' % quote_block

class RequireSnippet():

    """Class to create snippet to insert for require statement."""

    def __init__(self, name, path,
                 should_add_var_name, should_add_var_statement,
                 context_allows_semicolon,
                 view=None,
                 file_name=None,
                 exports=None,
                 destructuring=False):
        """Constructor for RequireSnippet class."""
        self.view = view
        self.name = name
        self.path = path
        self.should_add_var_name = should_add_var_name
        self.should_add_var_statement = should_add_var_statement
        self.context_allows_semicolon = context_allows_semicolon

        self.es6import = self.get_project_pref('import')
        if self.es6import == 'detect': self.detect_import()

        self.var_type = self.get_project_pref('var')
        if self.var_type not in ('var', 'const', 'let', 'import'):
            self.var_type = 'var'
        self.file_name = file_name
        self.jscs_options = dict()
        if self.file_name:
            self.jscs_options = get_jscs_options(self.file_name)
        self.exports = exports
        self.destructuring = destructuring or self.es6import

    def detect_import(self):
        """ Helper to determine whether to use es6 or require imports based on file context """
        if self.contains_match(CONTAINS_IMPORT): self.es6import = True
        elif self.contains_match(CONTAINS_REQUIRE): self.es6import = False
        else: self.es6import = self.get_project_pref('detect_prefer_imports')


    def contains_match(self, regexp):
        """
            Helper to determine whether a regexp is contained in the current file in sublime 3 or sublime 2
        """
        # If the regexp is not found, find will return a tuple (-1, -1) in Sublime 3 or None in Sublime 2 
        # https://github.com/SublimeTextIssues/Core/issues/534
        contains_import = self.view.find(regexp, 0)
        return contains_import.size() > 0 if float(sublime.version()) >= 3000 else contains_import is not None


    def get_formatted_code(self):
        """Return formatted code for insertion."""
        require_fmt = 'require({quote}{path}{quote})'
        import_fmt = 'import ${{1:{name}}}'
        import_fmt += ' from {quote}{path}{quote}'

        # promisification based on preferences
        promisify = self.promisify()
        if promisify:
            require_fmt = '%s(%s)' % (promisify, require_fmt)

        if self.exports:
            import_fmt = 'import {{ {exports} }} from {quote}{path}{quote}'

            if not self.destructuring:
                require_fmt = '%s {export} = %s.{export}' % (self.var_type,                                                             require_fmt)
            else:
                require_fmt = '%s {{ {exports} }} = %s' % (self.var_type,
                                                           require_fmt)

        else:
            # Add var statement based on preferences
            if self.should_add_var_name:
                require_fmt = '${{1:{name}}} = ' + require_fmt
                if self.should_add_var_statement:
                    require_fmt = self.var_type + ' ' + require_fmt

        # Add ;s depending on preferences and context
        if self._should_add_semicolon():
            require_fmt += ';'
            import_fmt += ';'

        # Handle whitespace stripping if necessary
        should_strip_setter_whitespace = self.should_strip_setter_whitespace()
        if should_strip_setter_whitespace['before']:
            require_fmt = re.sub(' =', '=', require_fmt)
        if should_strip_setter_whitespace['after']:
            require_fmt = re.sub('= ', '=', require_fmt)

        fmt = import_fmt if self.es6import else require_fmt

        if not self.should_use_snippet():
            fmt = strip_snippet_groups(fmt)

        if self.exports and not self.destructuring:
            return "\n".join([
                fmt.format(
                    name=self.name,
                    path=self.path,
                    quote=self.get_quotes(),
                    export=export
                )
                for export in self.exports
            ])

        return fmt.format(
            name=self.name,
            path=self.path,
            quote=self.get_quotes(),
            exports=", ".join(self.exports or [])
        )

    def get_args(self):
        """Return arguments for insert snippet command."""
        return {
            'contents': self.get_formatted_code()
        }

    def get_quotes(self):
        """Get type of quotes to use."""
        # However ignore the 'true' autodetection setting.
        jscs_quotes = self.jscs_options.get('validateQuoteMarks')
        if isinstance(jscs_quotes, dict):
            jscs_quotes = jscs_quotes.get('mark')
        if jscs_quotes and jscs_quotes is not True:
            return jscs_quotes

        # Use whatever quote type is set in preferences
        return get_quotes()

    def promisify(self):
        """Handle promise stuff."""
        if not self.get_project_pref('usePromisify'):
            return

        if self.path in self.get_project_pref('promisify'):
            return self.get_project_pref('promise').get('promisify')

        if self.path in self.get_project_pref('promisifyAll'):
            return self.get_project_pref('promise').get('promisifyAll')

        return None

    def _should_add_semicolon(self):
        return (should_add_semicolon(self.file_name) and
                self.context_allows_semicolon)

    def should_strip_setter_whitespace(self):
        """Parses the disallowSpace{After,Before}BinaryOperators
        jscs options and checks if spaces are not allowed before or
        after an `=` so we know if we should strip those from the
        var statement.
        """

        def parse_jscs_option(val):
            if type(val) == bool:
                return val

            if isinstance(val, list) and '=' in val:
                return True

            return False

        return dict(
            before=parse_jscs_option(
                self.jscs_options.get('disallowSpaceBeforeBinaryOperators')),
            after=parse_jscs_option(
                self.jscs_options.get('disallowSpaceAfterBinaryOperators'))
        )

    def should_use_snippet(self):
        return get_pref('snippet')

    def get_project_pref(self, key):
        return get_project_pref(key, view=self.view)
