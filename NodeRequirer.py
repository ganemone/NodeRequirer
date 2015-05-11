"""Contains classes for all NodeRequirer commands."""
import sublime
import sublime_plugin
import os
import re

from NodeRequirer.src import utils
from NodeRequirer.src.RequireSnippet import RequireSnippet
from NodeRequirer.src.modules import core_modules
from NodeRequirer.src.ModuleLoader import ModuleLoader

WORD_SPLIT_RE = re.compile(r"\W+")


class RequireFromWordCommand(sublime_plugin.TextCommand):

    """Text command for adding require statment from hovering over word."""

    def run(self, edit):
        """Called when the command is run."""
        self.edit = edit
        cursor = self.view.sel()[0]
        word_region = self.view.word(cursor)
        word_text = self.view.substr(word_region)

        self.module_loader = ModuleLoader(self.view.file_name())
        files = self.module_loader.get_file_list()

        module = utils.best_fuzzy_match(files, word_text)
        self.view.run_command('require_insert_helper', {
            'args': {
                'module': module,
                'type': 'word'
            }
        })


class RequireCommand(sublime_plugin.TextCommand):

    """Text Command which prompts for a module and inserts it into the file."""

    def run(self, edit, command):
        """Called when the command is run."""
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
            func = self.show_exports

        self.module_loader = ModuleLoader(self.view.file_name())
        self.files += self.module_loader.get_file_list()

        sublime.active_window().show_quick_panel(
            self.files, self.on_done_call_func(self.files, func))

    def on_path_entered(self, path):
        """When a path is entered, set the project data."""
        sublime.active_window().set_project_data({
            'folders': [{
                'path': path
            }]
        })

    def on_path_changed(self, text):
        """Do nothing when path is changed."""
        return None

    def on_canceled(self):
        """Send error message if user cancels after entering a path."""
        return sublime.error_message(
            'You must configure the absolute path '
            'for your project before using NodeRequirer. '
            'See the readme for more information.'
        )

    def on_done_call_func(self, choices, func):
        """Return a function which is used with sublime list picking."""
        def on_done(index):
            if index >= 0:
                return func(choices[index])

        return on_done

    def insert(self, module):
        """Run the insert helper command with the module selected."""
        self.view.run_command('require_insert_helper', {
            'args': {
                'module': module,
                'type': 'standard'
            }
        })

    def show_exports(self, module=None):
        """Prompt selection of exports for previously selected file."""
        if module is not None:
            self.selected_module = module
            self.exports += self.module_loader.get_exports(module)
        sublime.set_timeout(
            lambda: sublime.active_window().show_quick_panel(
                self.exports,
                self.on_export_done), 10
        )

    def on_export_done(self, index):
        """Handle selection of exports."""
        if index > 0:
            self.exports[0] = ['------ Finish Selecting ------']
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
        """Run export helper to insert selected exports into file."""
        self.view.run_command('export_insert_helper', {
            'args': {
                'module': self.selected_module,
                'exports': self.selected_exports
            }
        })


class SimpleRequireCommand(RequireCommand):

    """Command that calls the RequireCommand with the type argument simple."""

    def run(self, edit):
        """Called when the SimpleRequireCommand is run."""
        super().run(edit, 'simple')


class ExportRequireCommand(RequireCommand):

    """Command that calls the RequireCommand with the type argument export."""

    def run(self, edit):
        """Called when the ExportRequireCommand is run."""
        super().run(edit, 'export')


class ExportInsertHelperCommand(sublime_plugin.TextCommand):

    """Command that inserts a list of specific exports required."""

    def run(self, edit, args):
        """Insert require statement after the module exports are choosen."""
        module_info = get_module_info(args['module'], self.view)
        self.path = module_info['module_path']
        self.module_name = module_info['module_name']
        self.exports = args['exports']
        self.edit = edit

        content = self.get_content()
        position = self.view.sel()[0].begin()
        self.view.insert(self.edit, position, content)

    def get_content(self):
        """Get content to insert."""
        if len(self.exports) == 1:
            return self.get_single_export_content()
        return self.get_many_exports_content()

    def get_single_export_content(self):
        """Get content for a single export."""
        require_string = 'var {export} = require({q}{path}{q}).{export}'

        return require_string.format(
            export=self.exports.pop(),
            q=utils.get_quotes(),
            path=self.path
        )

    def get_many_exports_content(self):
        """Get content for many exports."""
        destruc = utils.get_pref('destructuring')
        if destruc is True:
            return self.get_many_exports_destructured()
        return self.get_many_exports_standard()

    def get_many_exports_destructured(self):
        """Get content for many exports with destructuring."""
        iter_exports = iter(self.exports)
        first_export = next(iter_exports)
        require_string = 'var {{{0}'.format(first_export)
        for export in iter_exports:
            require_string += ', {0}'.format(export)

        require_string += ' }} = require({q}{path}{q});'.format(
            path=self.path,
            q=utils.get_quotes()
        )

        return require_string

    def get_many_exports_standard(self):
        """Get content for many exports without destructuring."""
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

    """Command for inserting a basic require statement."""

    def run(self, edit, args):
        """Insert the require statement after the module has been choosen."""
        self.edit = edit

        is_from_word = (args['type'] == 'word')
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
        should_add_var_name = (not prev_text.endswith((':', '=')) and
                               not in_brackets)
        context_allows_semicolon = (not next_text.startswith((';', ',')) and
                                    not in_brackets)

        snippet = RequireSnippet(
            module_name,
            module_path,
            should_add_var_name=should_add_var_name,
            should_add_var_statement=should_add_var_statement,
            context_allows_semicolon=context_allows_semicolon,
            view=view,
            file_name=view.file_name()
        )
        if is_from_word:
            self.run_from_word(snippet)
        else:
            self.run_from_command(snippet)

    def run_from_word(self, snippet):
        """Insert a require statement from the ctrl+shift+o command.

        This command mimics the functionality of import-js in that
        the upon the command, the word under the cursor is used to
        determine which module to import. The module is then inserted
        at the bottom of the import list, rather than at the current
        cursor position.
        """
        cursor = self.view.sel()[0]
        prev_region = sublime.Region(0, cursor.begin())
        lines = self.view.lines(prev_region)
        region_for_insertion = None
        for line in lines:
            line_text = self.view.substr(line)
            if 'require' not in line_text and 'import' not in line_text:
                region_for_insertion = line
                break

        if region_for_insertion is None:
            region_for_insertion = self.view.line(cursor.begin())

        formatted_code = snippet.get_formatted_code() + '\n'
        self.view.insert(
            self.edit,
            region_for_insertion.begin(),
            formatted_code
        )

    def run_from_command(self, snippet):
        """Run the standard insert snippet command at the cursor position."""
        self.view.run_command('insert_snippet', snippet.get_args())

    def get_last_opened_bracket(self, text):
        """Return the last open bracket before the current cursor position."""
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
    """Get a dictionary with keys for the module_path and the module_name.

    In the case that the module is a node core module, the module_path and
    module_name are the same.
    """
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
