import sublime
import sublime_plugin
import os
import json
import re

HAS_REL_PATH_RE = re.compile(r"\.?\.?\/")
WORD_SPLIT_RE = re.compile(r"\W+")


class RequireCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.files = [
            'assert',
            'buffer',
            'cluster',
            'child_process',
            'crypto',
            'dgram',
            'dns',
            'domain',
            'events',
            'fs',
            'http',
            'https',
            'net',
            'os',
            'path',
            'punycode',
            'readline',
            'stream',
            'string_decoder',
            'tls',
            'url',
            'util',
            'vm',
            'zlib'
        ]

        project_data = sublime.active_window().project_data()
        project_folder = None

        if project_data:
            first_folder = project_data['folders'][0]['path']
            if os.path.exists(os.path.join(first_folder, 'package.json')):
                project_folder = first_folder

        if not project_folder:
            project_folder = self.find_project_folder()

        self.project_folder = project_folder
        self.load_file_list()

        sublime.active_window().show_quick_panel(self.files, self.insert)

    def find_project_folder(self):
        dirname = os.path.dirname(self.view.file_name())
        while dirname:
            if os.path.exists(os.path.join(dirname, 'package.json')):
                return dirname
            parent = os.path.abspath(os.path.join(dirname, os.pardir))
            if parent == dirname:
                break
            dirname = parent

    def load_file_list(self):
        self.parse_package_json()
        dirname = os.path.dirname(self.view.file_name())
        walk = os.walk(self.project_folder)
        for root, dirs, files in walk:
            if 'node_modules' in dirs:
                dirs.remove('node_modules')
            if '.git' in dirs:
                dirs.remove('.git')
            for file_name in files:
                if file_name[0] is not '.':
                    file_name = "%s/%s" % (root, file_name)
                    file_name = os.path.relpath(file_name, dirname)

                    if file_name == os.path.basename(self.view.file_name()):
                        continue

                    if not HAS_REL_PATH_RE.match(file_name):
                        file_name = "./%s" % file_name

                self.files.append(file_name)

    def parse_package_json(self):
        package = os.path.join(self.project_folder, 'package.json')
        package_json = json.load(open(package, 'r'))
        dependency_types = (
            'dependencies',
            'devDependencies',
            'optionalDependencies'
        )
        for dependency_type in dependency_types:
            if dependency_type in package_json:
                self.files += package_json[dependency_type].keys()

    def insert(self, index):
        if index >= 0:
            module = self.files[index]
            position = self.view.sel()[-1].end()
            self.view.run_command('require_insert_helper', {
                'args': {
                    'position': position,
                    'module': module
                }
            })


class RequireInsertHelperCommand(sublime_plugin.TextCommand):

    def run(self, edit, args):
        """Insert the require statement after the module has been choosen"""

        module_info = self.get_module_info(args['module'])
        module_path = module_info['module_path']
        module_name = module_info['module_name']

        quotes = "'" if PluginUtils.get_pref('quotes') == 'single' else '"'

        view = self.view

        cursor = view.sel()[0]
        prev_text = view.substr(sublime.Region(0, cursor.begin())).strip()
        last_bracket = self.get_last_opened_bracket(prev_text)
        in_brackets = last_bracket in ('(', '[')
        last_word = re.split(WORD_SPLIT_RE, prev_text)[-1]
        should_add_var_statement = (
            not prev_text.endswith(',') and
            last_word not in ('var', 'const', 'let')
        )
        should_add_var = (not prev_text.endswith((':', '=')) and
                          not in_brackets)

        snippet = RequireSnippet(module_name, module_path, quotes,
                                 should_add_var, should_add_var_statement)
        view.run_command('insert_snippet', snippet.get_args())

    def get_last_opened_bracket(self, text):
        """Return the last open bracket before the current cursor position"""
        counts = [(pair, text.count(pair[0]) - text.count(pair[1]))
                  for pair in ('()', '[]', '{}')]

        last_idx = -1
        last_bracket = None
        for pair, count in counts:
            idx = text.rfind(pair[0])
            if idx > last_idx and count > 0:
                (last_idx, last_bracket) = (idx, pair[0])
        return last_bracket

    def get_module_info(self, module_path):
        """Gets a dictionary with keys for the module_path and the module_name.
        In the case that the module is a node core module, the module_path and
        module_name are the same."""

        aliases = PluginUtils.get_pref('alias')
        omit_extensions = PluginUtils.get_pref('omit_extensions')

        if module_path in aliases:
            module_name = aliases[module_path]
        else:
            module_name = os.path.basename(module_path)
            module_name, extension = os.path.splitext(module_name)

            # When requiring an index.js file, rename the
            # var as the directory directly above
            if module_name == 'index' and extension == ".js":
                module_path = os.path.dirname(module_path)
                module_name = os.path.split(module_path)[-1]
                if module_name == '':
                    current_file = view.file_module_name()
                    directory = os.path.dirname(current_file)
                    module_name = os.path.split(directory)[-1]
            # Depending on preferences, remove the file extension
            elif omit_extensions and module_path.endswith(tuple(omit_extensions)):
                module_path = os.path.splitext(module_path)[0]

            # Capitalize modules named with dashes
            # i.e. some-thing => SomeThing
            dash_index = module_name.find('-')
            while dash_index > 0:
                first = module_name[:dash_index].capitalize()
                second = module_name[dash_index + 1:].capitalize()
                module_name = '{fst}{snd}'.format(fst=first, snd=second)
                dash_index = module_name.find('-')

        # Fix paths for windows
        if os.sep != '/':
            module_path = module_path.replace(os.sep, '/')

        return {
            'module_path': module_path,
            'module_name': module_name
        }


class RequireSnippet():

    def __init__(self, name, path, quotes,
                 should_add_var, should_add_var_statement):
        self.name = name
        self.path = path
        self.quotes = quotes
        self.should_add_var = should_add_var
        self.should_add_var_statement = should_add_var_statement
        self.es6import = PluginUtils.get_pref('import')
        self.var_type = PluginUtils.get_pref('var')
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

# Taken from Sublime JSHint Gutter
SETTINGS_FILE = "NodeRequirer.sublime-settings"


class PluginUtils:

    @staticmethod
    def get_pref(key):
        return sublime.load_settings(SETTINGS_FILE).get(key)
