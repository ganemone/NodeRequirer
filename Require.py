import sublime, sublime_plugin
import os, json

class RequireCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    self.files = [
      'assert',
      'cluster',
      'child_process',
      'dgram',
      'dns',
      'events',
      'fs',
      'http',
      'https',
      'net',
      'os',
      'path',
      'punycode',
      'readline',
      'string_decoder',
      'tls',
      'url',
      'util',
      'vm',
      'zlib'
    ]
    self.project_folder = sublime.active_window().project_data()['folders'][0]['path']
    self.load_file_list()

    sublime.active_window().show_quick_panel(self.files, self.insert)

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

          if '/' not in file_name:
            file_name = "./%s" % file_name

        self.files.append(file_name)

  def parse_package_json(self):
    package = os.path.join(self.project_folder, 'package.json')

    f = open(package, 'r')
    package_json = json.load(f)

    all_dependencies = list(package_json['dependencies']) + list(package_json['devDependencies'])

    self.files = self.files + all_dependencies


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
    module = args['module'];
    module_name = os.path.basename(module)
    extension_index = module_name.find('.')
    extension = ''
    if extension_index > 0:
      extension = module_name[:-extension_index]
      module_name = module_name[:extension_index]


    if 'models' in module:
      module_name = module_name.capitalize()

    if 'collections' in module:
      module_name = module_name.capitalize()

    if module_name == 'index':
      temp_module = module[:5 + len(extension) + 1]
      module_name = os.path.basename(temp_module)


    dash_index = module_name.find('-')
    while dash_index > 0:
      module_name = "%s%s" % (module_name[:dash_index].capitalize(), module_name[dash_index + 1:].capitalize())
      dash_index = module_name.find('-')

    text_to_insert = "var %s = require('%s');" % (module_name, module)

    self.view.insert(edit, args['position'], text_to_insert)

