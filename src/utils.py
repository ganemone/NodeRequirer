import sublime
import os
import io
import json
import re
from io import StringIO

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


def aliased(module_path):
    aliases = get_pref('alias')
    alias_patterns = get_pref('alias-pattern')

    if module_path in aliases:
        return aliases[module_path]

    for alias_pattern, result_pattern in alias_patterns.items():
        m = re.match(alias_pattern, module_path)
        if m:
            return m.expand(result_pattern)

    return None

def strip_snippet_groups(snippet_text):
    """
    This (admittedly complex looking) function goes through a snippet string and strips
    out the groups (`${{1}}` and `${{2:content}}`) leaving any default text in their place.

    It's somewhat complex since it iterates through matches on `${{n}}`, `${{n:`, and `}}`
    and uses a stack to ensure that nested groups (`${{1:...${{2:...}}...}}`) work correctly
    and `}}`'s that do not belong to a group are not discarded.
    """
    r = re.compile('\$\{\{(\d+)(:|\}\})|(\}\})')
    pos = 0
    stack = []
    out = StringIO()
    while True:
        m = r.search(snippet_text, pos)
        if m:
            out.write(snippet_text[pos:m.start()])
            start_num, mid, end = m.group(1, 2, 3)
            if end:
                if len(stack) > 0:
                    _out, _ = stack.pop()
                    _out.write(out.getvalue())
                    out.close()
                    out = _out
                else:
                    out.write(end)
            elif mid == '}}':
                pass
            else:
                stack.append((out, m.group()))
                out = StringIO()
            pos = m.end()
        else:
            out.write(snippet_text[pos:])
            break
    while len(stack) > 0:
        _out, tail = stack.pop()
        _out.write(out.getvalue())
        _out.write(tail)
        out.close()
        out = _out

    snippet_text = out.getvalue()
    out.close()

    return snippet_text


def lazy_parse_comment_json(json_text):
	"""
	This attempts to parse files like .jscsrc which are .json files with
	comments in them.

	This is lazy in that we simply strip things with a regexp and don't take string boundaries into account.
	This should be fine since it's unlikely that any of the config options we want contain comment-like text
	"""

	if isinstance(json_text, io.IOBase):
		json_text = json_text.read()

	json_text = re.sub(r'(#|//).*$', '', json_text, re.MULTILINE)
	json_text = re.sub(r'/\*.*\*/', '', json_text, re.DOTALL)
	return json.loads(json_text)


def get_jscs_options(path):
	option_sets = []

	jscsrc_path = findup(path, '.jscsrc')
	if os.path.isfile(jscsrc_path):
		jscsrc = lazy_parse_comment_json(open(jscsrc_path, 'r', encoding='UTF-8'))
		option_sets.append((jscsrc_path, jscsrc))

	jscs_json_path = findup(path, '.jscs.json')
	if os.path.isfile(jscs_json_path):
		jscs_json = json.load(open(jscs_json_path, 'r', encoding='UTF-8'))
		option_sets.append((jscs_json_path, jscs_json))

	package_path = findup(path, 'package.json')
	if os.path.isfile(package_path):
		package = json.load(open(package_path, 'r', encoding='UTF-8'))
		if 'jscsConfig' in package:
			option_sets.append((package_path, package['jscsConfig']))

	# Sort sets by dirname length
	option_sets.sort(key=lambda x: len(os.path.dirname(x[0])))

	# Merge options together
	options = dict()
	for path, option_set in option_sets:
		options.update(option_set)

	return options

def findup(path, relative_path):
	path = os.path.abspath(path)
	# Testing path against dirname(path) should be more reliable than testing it against '/'
	# and work on Windows where root may be C:/ or something else.
	while path and path != os.path.dirname(path):
		test_path = os.path.join(path, relative_path)
		if os.path.isfile(test_path):
			return test_path

		path = os.path.dirname(path)

	return False
