"""This file contains the ModuleLoader class."""
import sublime
import os
import re
import json

from NodeRequirer.src import utils

HAS_REL_PATH_RE = re.compile(r"\.?\.?\/")
IS_EXPORT_LINE = re.compile(r"exports\.(.*?)=")


class ModuleLoader():

    """Class which handles shared functionality for require commands."""

    def __init__(self, file_name):
        """Constructor for ModuleLoader."""
        self.file_name = file_name
        self.project_folder = self.get_project_folder()

        # If there is no package.json, show error
        if not self.has_package() and not self.has_bower():
            return sublime.error_message(
                'You must have a package.json and or bower.json file '
                'in your projects root directory'
            )

    def has_package(self):
        """Check if the package.json is in the project directory."""
        return os.path.exists(
            os.path.join(self.project_folder, 'package.json')
        )

    def has_bower(self):
        """Check if a bower.json is in the project directory."""
        return os.path.exists(
            os.path.join(self.project_folder, 'bower.json')
        )

    def get_project_folder(self) -> str:
        """Get the root project folder."""
        # Walk through directories if we didn't find it easily
        dirname = os.path.dirname(self.file_name)
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

    def get_file_list(self):
        """Return the list of dependencies and local files."""
        files = self.get_local_files() + self.get_dependencies()
        exclude_patterns = utils.file_exclude_patterns()

        def should_include_file(file):
            for pattern in exclude_patterns:
                if pattern in file:
                    return False
            return True
        files = list(filter(
            lambda f: should_include_file(f), files
        ))
        return files

    def get_local_files(self):
        """Load the list of local files."""
        # Don't throw errors if invoked in a view without
        # a filename like the console
        local_files = []
        if not self.file_name:
            return []

        dirname = os.path.dirname(self.file_name)
        exclude = utils.dirs_to_exclude()
        for root, dirs, files in os.walk(self.project_folder, topdown=True):
            if os.path.samefile(root, self.project_folder):
                dirs[:] = [d for d in dirs if d not in exclude]

            for file_name in files:
                if file_name[0] is not '.':
                    file_name = "%s/%s" % (root, file_name)
                    file_name = os.path.relpath(file_name, dirname)

                    if file_name == os.path.basename(self.file_name):
                        continue

                    if not HAS_REL_PATH_RE.match(file_name):
                        file_name = "./%s" % file_name

                local_files.append(file_name)
        return local_files

    def get_dependencies(self):
        """Load project dependencies."""
        deps = []
        if self.has_bower():
            deps += self.get_bower_dependencies()
        if self.has_package():
            deps += self.get_package_dependencies()
        return deps

    def get_bower_dependencies(self):
        """Parse the bower.json file into a list of dependencies."""
        bower_path = os.path.join(self.project_folder, 'bower.json')
        bower = json.load(open(bower_path, 'r', encoding='UTF-8'))
        dependency_types = (
            'dependencies',
            'devDependencies'
        )
        return self.get_dependencies_with_type(dependency_types, bower)

    def get_package_dependencies(self):
        """Parse the package.json file into a list of dependencies."""
        package = os.path.join(self.project_folder, 'package.json')
        package_json = json.load(open(package, 'r', encoding='UTF-8'))
        dependency_types = (
            'dependencies',
            'devDependencies',
            'optionalDependencies'
        )
        dependencies = self.get_dependencies_with_type(
            dependency_types, package_json
        )
        modules_path = os.path.join(self.project_folder, 'node_modules')
        dep_files = self.get_dependency_files(dependencies, modules_path)
        return dependencies + dep_files

    def get_dependencies_with_type(self, dependency_types, json):
        """Common function for adding dependencies (bower or package.json)."""
        dependencies = []
        for dependency_type in dependency_types:
            if dependency_type in json:
                dependencies += json[dependency_type].keys()
        return dependencies

    def get_dependency_files(self, dependencies, modules_path):
        """Walk through deps to allow requiring of files in deps package."""
        files_to_return = []
        for dependency in dependencies:
            module_path = os.path.join(modules_path, dependency)
            if not os.path.exists(module_path):
                return []

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
                    files_to_return.append(os.path.join(dependency, rel_path))
        return files_to_return

    def get_exports(self, module):
        """get a given modules exports (commonjs style)."""
        # Module is core module
        if utils.is_core_module(module):
            return self.get_core_module_exports()
        elif utils.is_local_file(module):
            dirname = os.path.dirname(self.file_name)
            path = os.path.join(dirname, module)
            return self.get_exports_in_file(path)
        else:
            return self.get_dependency_module_exports(module)

    def get_core_module_exports(self):
        """TODO: get the core module exports."""
        sublime.error_message(
            'Parsing node core module exports is not yet '
            'implemented. Feel free to submit a PR!'
        )

    def get_dependency_module_exports(self, module):
        """get a deps exports (commonjs)."""
        base_path = os.path.join(
            self.project_folder, 'node_modules', module
        )
        pkg_path = os.path.join(base_path, 'package.json')
        package = json.load(open(pkg_path, 'r', encoding='UTF-8'))
        main = 'index.js' if 'main' not in package else package['main']
        main_path = os.path.join(base_path, main)
        return self.get_exports_in_file(main_path)

    def get_exports_in_file(self, fpath):
        """get exports in a given file (commonjs)."""
        exports = []
        f = open(fpath, 'r')
        for line in f:
            result = re.search(IS_EXPORT_LINE, line)
            if result:
                exports.append(result.group(1).strip())

        if len(exports) <= 1:
            return sublime.error_message(
                'Unable to find specific exports. Note: We currently'
                ' only support parsing commonjs style exporting'
            )
        return exports
