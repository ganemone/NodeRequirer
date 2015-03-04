import sublime
from .modules import core_modules

SETTINGS_FILE = "NodeRequirer.sublime-settings"


def get_pref(key):
    return sublime.load_settings(SETTINGS_FILE).get(key)


def get_quotes():
    return "'" if get_pref('quotes') == 'single' else '"'


def is_core_module(module):
    return module in core_modules


def is_local_file(module):
    return '/' in module
