import sublime
import sublime_plugin
import os
import json
import re

from NodeRequirer.src import utils
from NodeRequirer.src.RequireSnippet import RequireSnippet
from NodeRequirer.src.modules import core_modules

HAS_REL_PATH_RE = re.compile(r"\.?\.?\/")
WORD_SPLIT_RE = re.compile(r"\W+")
IS_EXPORT_LINE = re.compile(r"exports\.(.*?)=")


class RequireCommand(sublime_plugin.TextCommand):

    """Text Command to prompt the user for a module, and upon
    selection insert it into the current view"""

    def run(self, edit, command):
        self.edit = edit
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
        # If there is no package.json, show error
        # TODO add support for bower
        if not self.has_package() and not self.has_bower():
            return sublime.error_message(
                'You must have a package.json and or bower.json file '
                'in your projects root directory'
            )

        if self.project_folder is None:
            current_dir = os.path.dirname(self.view.file_name())
            return sublime.active_window().show_input_panel(
                'Please enter the absolute path to your project folder',
                current_dir,
                self.on_path_entered,
                self.on_path_changed,
                self.on_canceled
            )

        self.load_file_list()

        sublime.active_window().show_quick_panel(
            self.files, self.on_done_call_func(self.files, func))

    def has_package(self):
        return os.path.exists(
            os.path.join(self.project_folder, 'package.json')
        )

    def has_bower(self):
        return os.path.exists(
            os.path.join(self.project_folder, 'bower.json')
        )

    def on_path_entered(self, path):
        sublime.active_window().set_project_data({
            'folders': [{
                'path': path
            }]
        })

    def on_path_changed(self, text):
        return None

    def on_canceled(self):
        return sublime.error_message(
            'You must configure the absolute path '
            'for your project before using NodeRequirer. '
            'See the readme for more information.'
        )

    def get_project_folder(self) -> str:
        # Walk through directories if we didn't find it easily
        dirname = os.path.dirname(self.view.file_name())
        while dirname:
            pkg = os.path.join(dirname, 'package.json')
            bwr = os.path.join(dirname, 'bower.json')
            if os.path.exists(pkg) or os.path.exists(bwr):
                return dirname
            parent = os.path.abspath(os.path.join(dirname, os.pardir))
            if parent == dirname:
                break
            dirname = parent

        try:
            project_data = sublime.active_window().project_data()
            if project_data:
                print('Project Data: {0}'.format(project_data))
                first_folder = project_data['folders'][0]['path']
                return first_folder
        except:
            pass
        sublime.error_message(
            'Can\'t find a package.json or bower.json corresponding to your '
            'project. If you don\'t have one of these, you must specify the '
            'full path to your project in a .sublime-project file. See the '
            'README for more details'
        )

    def load_file_list(self):
        self.get_dependencies()
        self.get_local_files()

    def get_local_files(self):
        # Don't throw errors if invoked in a view without
        # a filename like the console
        if not self.view.file_name():
            print('Not in a file, ignoring local files.')
            return

        dirname = os.path.dirname(self.view.file_name())
        exclude = set(['node_modules', '.git',
                       'bower_components', 'components'])
        for root, dirs, files in os.walk(self.project_folder, topdown=True):
            if os.path.samefile(root, self.project_folder):
                dirs[:] = [d for d in dirs if d not in exclude]
                print('Removing Dirs')

            for file_name in files:
                if file_name[0] is not '.':
                    file_name = "%s/%s" % (root, file_name)
                    file_name = os.path.relpath(file_name, dirname)

                    if file_name == os.path.basename(self.view.file_name()):
                        continue

                    if not HAS_REL_PATH_RE.match(file_name):
                        file_name = "./%s" % file_name

                self.files.append(file_name)

    def get_dependencies(self):
        if self.has_bower():
            self.parse_bower()
        if self.has_package():
            self.parse_package()

    def parse_bower(self):
        bower_path = os.path.join(self.project_folder, 'bower.json')
        bower = json.load(open(bower_path, 'r', encoding='UTF-8'))
        dependency_types = (
            'dependencies',
            'devDependencies'
        )
        self.add_dependencies(dependency_types, bower)

    def parse_package(self):
        package = os.path.join(self.project_folder, 'package.json')
        package_json = json.load(open(package, 'r', encoding='UTF-8'))
        dependency_types = (
            'dependencies',
            'devDependencies',
            'optionalDependencies'
        )
        dependencies = self.add_dependencies(dependency_types, package_json)
        modules_path = os.path.join(self.project_folder, 'node_modules')
        self.walk_dependencies(dependencies, modules_path)

    def add_dependencies(self, dependency_types, json):
        dependencies = []
        for dependency_type in dependency_types:
            if dependency_type in json:
                dependencies += json[dependency_type].keys()
        self.files += dependencies
        return dependencies

    def walk_dependencies(self, dependencies, modules_path):
        for dependency in dependencies:
            module_path = os.path.join(modules_path, dependency)
            if not os.path.exists(module_path):
                return

            walk = os.walk(module_path)
            for root, dirs, files in walk:
                if 'node_modules' in dirs:
                    dirs.remove('node_modules')
                for file_name in files:
                    basename = os.path.basename(file_name)
                    if not file_name.endswith('.js') or basename == 'index.js':
                        continue
                    full_path = os.path.join(root, file_name)
                    rel_path = os.path.relpath(full_path, module_path)
                    self.files.append(os.path.join(dependency, rel_path))

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
        if utils.is_core_module(module):
            return self.parse_core_module_exports()
        elif utils.is_local_file(module):
            dirname = os.path.dirname(self.view.file_name())
            path = os.path.join(dirname, module)
            print(path)
            return self.parse_exports_in_file(path)
        else:
            return self.parse_dependency_module_exports()

    def parse_core_module_exports(self):
        sublime.error_message(
            'Parsing node core module exports is not yet '
            'implemented. Feel free to submit a PR!'
        )

    def parse_dependency_module_exports(self):
        base_path = os.path.join(
            self.project_folder, 'node_modules', self.module
        )
        pkg_path = os.path.join(base_path, 'package.json')
        package = json.load(open(pkg_path, 'r', encoding='UTF-8'))
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
                self.exports,
                self.on_export_done), 10
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
        self.module_name = module_info['module_name']
        self.exports = args['exports']
        self.edit = edit

        content = self.get_content()
        position = self.view.sel()[0].begin()
        self.view.insert(self.edit, position, content)

    def get_content(self):
        if len(self.exports) == 1:
            return self.get_single_export_content()
        return self.get_many_exports_content()

    def get_single_export_content(self):
        require_string = 'var {export} = require({q}{path}{q}).{export}'

        return require_string.format(
            export=self.exports.pop(),
            q=utils.get_quotes(),
            path=self.path
        )

    def get_many_exports_content(self):
        destruc = utils.get_pref('destructuring')
        if destruc is True:
            return self.get_many_exports_destructured()
        return self.get_many_exports_standard()

    def get_many_exports_destructured(self):
        iter_exports = iter(self.exports)
        first_export = next(iter_exports)
        require_string = 'var {{{0}'.format(first_export)
        print('Inside many exports destructured')
        for export in iter_exports:
            require_string += ', {0}'.format(export)

        require_string += ' }} = require({q}{path}{q});'.format(
            path=self.path,
            q=utils.get_quotes()
        )

        return require_string

    def get_many_exports_standard(self):
        quotes = utils.get_quotes()
        require_string = 'var {module} = require({q}{path}{q});'.format(
            module=self.module_name,
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

        view = self.view

        cursor = view.sel()[0]
        prev_text = view.substr(sublime.Region(0, cursor.begin())).strip()
        next_text = view.substr(
            sublime.Region(cursor.end(), cursor.end() + 80)).strip()
        last_bracket = self.get_last_opened_bracket(prev_text)
        in_brackets = last_bracket in ('(', '[')
        last_word = re.split(WORD_SPLIT_RE, prev_text)[-1]
        should_add_var_statement = (
            not prev_text.endswith(',') and
            last_word not in ('var', 'const', 'let')
        )
        should_add_var = (not prev_text.endswith((':', '=')) and
                          not in_brackets)
        context_allows_semicolon = (not next_text.startswith((';', ',')) and
                                    not in_brackets)

        snippet = RequireSnippet(
            module_name,
            module_path,
            should_add_var=should_add_var,
            should_add_var_statement=should_add_var_statement,
            context_allows_semicolon=context_allows_semicolon,
            view=view,
            file_name=view.file_name()
        )
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

    aliased_to = utils.aliased(module_path, view=view)
    omit_extensions = utils.get_project_pref('omit_extensions', view=view)

    if aliased_to:
        module_name = aliased_to
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
