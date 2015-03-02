import sublime
import sublime_plugin
import os
import json
import re

from NodeRequirer.src.utils import get_pref, get_quotes
from NodeRequirer.src.RequireSnippet import RequireSnippet
from NodeRequirer.src.modules import core_modules

HAS_REL_PATH_RE = re.compile(r"\.?\.?\/")
WORD_SPLIT_RE = re.compile(r"\W+")
IS_EXPORT_LINE = re.compile(r"exports\.(.*?)=")


class RequireCommand(sublime_plugin.TextCommand):

    def run(self, edit, command):
        # Simple Require Command
        if command is 'simple':
            # Must copy the core modules so modifying self.files
            # does not change the core_modules list
            self.files = list(core_modules)
            func = self.insert
        # Export Command
        else:
            self.files = []
            self.exports = ['------ Select One or More Options ------']
            self.selected_exports = []
            func = self.parse_exports

        self.project_folder = self.get_project_folder()
        self.load_file_list()

        sublime.active_window().show_quick_panel(
            self.files, self.on_done_call_func(self.files, func))

    def get_project_folder(self):
        project_data = sublime.active_window().project_data()

        if project_data:
            first_folder = project_data['folders'][0]['path']
            if os.path.exists(os.path.join(first_folder, 'package.json')):
                return first_folder

        # Walk through directories if we didn't find it easily
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
        package_json = json.load(open(package, 'r', encoding='UTF-8'))
        dependency_types = (
            'dependencies',
            'devDependencies',
            'optionalDependencies'
        )
        for dependency_type in dependency_types:
            if dependency_type in package_json:
                self.files += package_json[dependency_type].keys()

    def on_done_call_func(self, choices, func):
        def on_done(index):
            if index >= 0:
                return func(choices[index])

        return on_done

    def insert(self, module):
        self.view.run_command('require_insert_helper', {
            'args': {
                'module': module
            }
        })

    def parse_exports(self, module):
        self.module = module
        # Module is core module
        if is_core_module(module):
            return self.parse_core_module_exports()
        elif is_local_file(module):
            return self.parse_exports_in_file(module)
        else:
            return self.parse_dependency_module_exports()

    def parse_core_module_exports(self):
        print('I dont know how to do this just yet')

    def parse_dependency_module_exports(self):
        base_path = './node_modules/' + self.module
        package = json.load(
            open(base_path + '/package.json', 'r', encoding='UTF-8'))
        main = 'index.js' if 'main' not in package else package['main']
        main_path = os.path.join(base_path, main)
        return self.parse_exports_in_file(main_path)

    def parse_exports_in_file(self, fpath):
        f = open(fpath, 'r')
        for line in f:
            result = re.search(IS_EXPORT_LINE, line)
            if result:
                self.exports.append(result.group(1).strip())

        if len(self.exports) <= 1:
            return sublime.error_message(
                'Unable to find specific exports. Note: We currently'
                ' only support parsing commonjs style exporting'
            )
        return self.show_exports()

    def show_exports(self):
        sublime.set_timeout(
            lambda: sublime.active_window().show_quick_panel(
                self.exports, self.on_export_done), 10
        )

    def on_export_done(self, index):
        if index > 0:
            self.exports[0] = '------ Finish Selecting ------'
            # Add selected export to selected_exports list and
            # remove it from the list
            self.selected_exports.append(self.exports.pop(index))

            if len(self.exports) > 1:
                # Show remaining exports for further selection
                self.show_exports()
            elif len(self.selected_exports) > 0:
                # insert current selected exports
                self.insert_exports()
        elif index == 0 and len(self.selected_exports) > 0:
            # insert current selected exports
            self.insert_exports()

    def insert_exports(self):
        self.view.run_command('export_insert_helper', {
            'args': {
                'module': self.module,
                'exports': self.selected_exports
            }
        })


class SimpleRequireCommand(RequireCommand):

    """Helper command to call the RequireCommand with the
    type argument 'simple'"""

    def run(self, edit):
        super().run(edit, 'simple')


class ExportRequireCommand(RequireCommand):

    """Helper command to call the RequireCommand with the
    type argument 'export'"""

    def run(self, edit):
        super().run(edit, 'export')


class ExportInsertHelperCommand(sublime_plugin.TextCommand):

    def run(self, edit, args):
        """Insert the require statement after the module
        exports have been choosen"""
        module_info = get_module_info(args['module'], self.view)
        self.path = module_info['module_path']
        self.name = module_info['module_name']
        self.exports = args['exports']
        self.edit = edit

        content = self.get_content()
        self.view.run_command('insert_snippet', {
            'contents': content
        })

    def get_content(self):
        if len(self.exports) == 1:
            return self.get_single_export_content()
        return self.get_many_exports_content()

    def get_single_export_content(self):
        return 'var {export} = require({q}{path}{q}).{export};'.format(
            export=self.exports[0],
            q=get_quotes(),
            path=self.path
        )

    def get_many_exports_content(self):
        destruc = get_pref('destructuring')
        if destruc is True:
            return self.get_many_exports_destructured()
        return self.get_many_exports_standard()

    def get_many_exports_destructured(self):
        iter_exports = iter(self.exports)
        first_export = next(iter_exports)
        require_string = 'var {{{0}'.format(first_export)

        for export in iter_exports:
            require_string += ', {0}'.format(export)

        require_string += ' }} = require({q}{path}{q});'.format(
            path=self.path,
            q=get_quotes()
        )

        return require_string

    def get_many_exports_standard(self):
        quotes = get_quotes()
        require_string = 'var {module} = require({q}{path}{q});'.format(
            module=self.name,
            q=quotes,
            path=self.path
        )
        for export in self.exports:
            require_string += '\n'
            final = 'var {export} = require({q}{path}{q}).{export};'
            require_string += final.format(
                export=export,
                q=quotes,
                path=self.path
            )

        return require_string


class RequireInsertHelperCommand(sublime_plugin.TextCommand):

    def run(self, edit, args):
        """Insert the require statement after the module has been choosen"""
        module_info = get_module_info(args['module'], self.view)
        module_path = module_info['module_path']
        module_name = module_info['module_name']

        quotes = get_quotes()

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


def get_module_info(module_path, view):
    """Gets a dictionary with keys for the module_path and the module_name.
    In the case that the module is a node core module, the module_path and
    module_name are the same."""

    aliases = get_pref('alias')
    omit_extensions = get_pref('omit_extensions')

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


def is_core_module(module):
    return module in core_modules


def is_local_file(module):
    return '/' in module
