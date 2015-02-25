import sublime

SETTINGS_FILE = "NodeRequirer.sublime-settings"

def get_pref(key):
    return sublime.load_settings(SETTINGS_FILE).get(key)

def get_quotes():
    return "'" if get_pref('quotes') == 'single' else '"'