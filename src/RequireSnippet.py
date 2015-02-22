from .utils import get_pref

class RequireSnippet():

    def __init__(self, name, path, quotes,
                 should_add_var, should_add_var_statement):
        self.name = name
        self.path = path
        self.quotes = quotes
        self.should_add_var = should_add_var
        self.should_add_var_statement = should_add_var_statement
        self.es6import = get_pref('import')
        self.var_type = get_pref('var')
        if self.var_type not in ('var', 'const', 'let'):
            self.var_type = 'var'

    def get_formatted_code(self):
        require_fmt = 'require({quote}{path}{quote});'
        import_fmt = 'import ${{1:{name}}} ${{2:as ${{3:somename}}}}'
        import_fmt += ' from {quote}{path}{quote};'
        fmt = None

        if self.es6import:
            fmt = import_fmt
        elif self.should_add_var:
            fmt = '${{1:{name}}} = ' + require_fmt
            if self.should_add_var_statement:
                fmt = self.var_type + ' ' + fmt
        else:
            fmt = require_fmt

        return fmt.format(
            name=self.name,
            path=self.path,
            quote=self.quotes
        )

    def get_args(self):
        return {
            'contents': self.get_formatted_code()
        }