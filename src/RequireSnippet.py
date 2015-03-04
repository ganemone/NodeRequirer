from .utils import get_pref, get_quotes, get_jscs_options

class RequireSnippet():

    def __init__(self, name, path,
                 should_add_var, should_add_var_statement,
                 context_allows_semicolon,
                 file_name=None):
        self.name = name
        self.path = path
        self.should_add_var = should_add_var
        self.should_add_var_statement = should_add_var_statement
        self.context_allows_semicolon = context_allows_semicolon
        self.es6import = get_pref('import')
        self.var_type = get_pref('var')
        if self.var_type not in ('var', 'const', 'let'):
            self.var_type = 'var'
        self.file_name = file_name
        self.jscs_options = dict()
        if self.file_name:
            self.jscs_options = get_jscs_options(self.file_name)

    def get_formatted_code(self):
        should_use_snippet = self.should_use_snippet()
        should_add_semicolon = self.should_add_semicolon()
        require_fmt = 'require({quote}{path}{quote});'
        import_fmt = 'import {name} from {quote}{path}{quote}'

        if should_use_snippet:
            import_fmt = 'import ${{1:{name}}} ${{2:as ${{3:somename}}}}'
            import_fmt += ' from {quote}{path}{quote};'
            if self.should_add_var:
                require_fmt = '${{1:{name}}} = ' + require_fmt
        elif self.should_add_var:
            require_fmt = '{name} = ' + require_fmt
            if self.should_add_var_statement:
                require_fmt = self.var_type + ' ' + require_fmt

        if not should_add_semicolon:
            require_fmt = require_fmt.rstrip(';')

        fmt = import_fmt if self.es6import else require_fmt

        return fmt.format(
            name=self.name,
            path=self.path,
            quote=self.get_quotes()
        )

    def get_args(self):
        return {
            'contents': self.get_formatted_code()
        }

    def get_quotes(self):
        # Allow explicit validateQuoteMarks rules to override the quote preferences
        # However ignore the 'true' autodetection setting.
        jscs_quotes = self.jscs_options.get('validateQuoteMarks')
        if isinstance(jscs_quotes, dict):
            jscs_quotes = jscs_quotes.get('mark')
        if jscs_quotes and jscs_quotes != True:
            return jscs_quotes

        # Use whatever quote type is set in preferences
        return get_quotes()

    def should_add_semicolon(self):
        # Ignore semicolons when jscs options say to
        if self.jscs_options.get('disallowSemicolons', False):
            return False

        if get_pref('semicolon_free'):
            return False

        return self.context_allows_semicolon

    def should_use_snippet(self):
        return get_pref('snippet')
