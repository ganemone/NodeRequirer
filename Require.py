import sublime, sublime_plugin
import os, json, re

has_rel_path = re.compile("\.?\.?\/")

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

          if not has_rel_path.match(file_name):
            file_name = "./%s" % file_name

        self.files.append(file_name)

  def parse_package_json(self):
    package = os.path.join(self.project_folder, 'package.json')
    package_json = json.load(open(package, 'r'))
    for dependencyType in ('dependencies', 'devDependencies', 'optionalDependencies'):
      if dependencyType in package_json:
        self.files += package_json[dependencyType].keys()


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
    aliases = PluginUtils.get_pref('alias')

    if module in aliases:
      module_name = aliases[module]
    else:
      module_name = os.path.basename(module)
      module_name, extension = os.path.splitext(module_name)
      if module_name == 'index':
        module_name = os.path.split(os.path.dirname(module))[-1]
        if module_name == '':
          module_name = os.path.split(os.path.dirname(self.view.file_name()))[-1]

      if module.endswith(".js"):
        module = module[:-3]

      dash_index = module_name.find('-')
      while dash_index > 0:
        module_name = "%s%s" % (module_name[:dash_index].capitalize(), module_name[dash_index + 1:].capitalize())
        dash_index = module_name.find('-')

    quote = "'" if PluginUtils.get_pref('quotes') == 'single' else '"'
    text_to_insert = 'var {name} = require({quote}{path}{quote});'.format(name=module_name, path=module, quote=quote)

    self.view.insert(edit, args['position'], text_to_insert)

# Taken from Sublime JSHint Gutter
SETTINGS_FILE = "Require.sublime-settings"

class PluginUtils:
  @staticmethod
  def get_pref(key):
    return sublime.load_settings(SETTINGS_FILE).get(key)
