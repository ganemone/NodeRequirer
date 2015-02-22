import sublime

SETTINGS_FILE = "NodeRequirer.sublime-settings"

def get_pref(key):
        return sublime.load_settings(SETTINGS_FILE).get(key)