# NodeRequirer - A Sublime Text 3 plugin for requiring node modules
#### [Sublime Text 3](http://www.sublimetext.com/3)

<a href='https://pledgie.com/campaigns/29265'><img alt='Click here to lend your support to: NodeRequirer Donations and make a donation at pledgie.com !' src='https://pledgie.com/campaigns/29265.png?skin_name=chrome' border='0' ></a>

## About
This is a Sublime Text 3 plugin allowing you to easily require node modules
without having to worry about relative paths. It parses your project to allow you
to require any local module or dependency listed in your package.json. In addition, it allows
you to include node core modules.

## Usage
`ctrl+shift+i` => `RequireCommand`

Provides a dropdown of local files, node core modules, and dependencies defined in package.json + bower.json
SublimeRequirer will insert `var {modulename} = require('/path/to/modulename.js')`.

![NodeRequirer](http://zippy.gfycat.com/FantasticEachAplomadofalcon.gif)

`ctrl+shift+e` => `RequireSpecificExportCommand`

Provides same initial drop down as `RequireCommand`. After selecting a module, the plugin will
attempt to parse the file or dependency to look for commonjs exports, and show a list of possible
exports. The user may then select one or more exports to be required.

Example with single export selection:
```javascript
var doSomething = require('../../utils/index.js').doSomething;
```

Example with multiple export selection:
```javascript
var utils = require('../../utils/index.js');
var doSomething = utils.doSomething;
var doAnotherThing = utils.doAnotherThing;
```
Or with the destructuring option in preferences set to true...
```javascript
var { doSomething, doAnotherThing } = require('../../utils/index.js');
```
![NodeRequireExport](http://zippy.gfycat.com/TanSnappyAngora.gif)

`ctrl+shift+o` => `RequireFromWordCommand`

With the cursor on the desired variable, press `ctrl+shift+o` to have NodeRequirer import
the corresponding module at the bottom of the current imports list. A fuzzy string matching
algorithm similar to how Sublime Text filters lists on user input is used to select the best
matching module to import. This is a new feature, and there still is some work to do on making
it work perfectly in all scenarios.

![RequireFromWordCommand](http://zippy.gfycat.com/HelpfulLastingHapuku.gif)

## Options

`NodeRequirer` exposes several useful plugin options for configuring aliases, import modes and quotes. These are available under `Preferences -> Package Settings -> Node Require` or search for `NodeRequirer: Set plugin options`

Example `User Plugin Preferences`

```javascript
{
    // Type of quotes to use
    "quotes": "single || double",
    
    // Use 'var', 'const', or 'let' variable declarations
    "var": "var",
    
    // Use ES6 import format, when syntactically correct. Use detect to determine based on file buffer
    "import": "detect",

    // Whether to use ES6 import or require in detect mode when
    // the format could not be identified (e.g. when neither were used in file)
    "detect_prefer_import": true,

    "alias": {
        // <module name>: <variable name>
        "underscore": "_"
    },

    // Use object destructuring when assigning multiple exports
    "destructuring": false,

    // Use snippets when inserting require statements to allow
    // for easy variable name changing
    "snippet": true,
    // Directories to exclude when searching for files to require
    // The default directories excluded are [".git", "bower_components", "node_modules"]
    "exclude_dirs": [".git", "bower_components", "node_modules", "somerandom_directory"],
    // File patterns to exclude. Basically does a substring search. Not very fancy
    // Default patterns: [".jpg", ".png", ".gif", ".md", "LICENSE", ".gitignore", "DS_STORE"]
    "file_exclude_patterns": []
}
```

## Installation
### Through [Sublime Package Manager](http://wbond.net/sublime_packages/package_control)

* `Ctrl+Shift+P` or `Cmd+Shift+P` in Linux/Windows/OS X
* type `install`, select `Package Control: Install Package`
* type `NodeRequirer`, select `NodeRequirer`

### Options

You can configure project aliases and quote options in the plugin options `ctrl+shift+p` and find *`NodeRequirer: Set Plugin Options`*

### Manually
Make sure you use the right Sublime Text folder. For example, on OS X, packages for version 2 are in `~/Library/Application\ Support/Sublime\ Text\ 2`, while version 3 is labeled `~/Library/Application\ Support/Sublime\ Text\ 3`.

These are for Sublime Text 3:

#### Mac
`git clone https://github.com/ganemone/NodeRequirer.git ~/Library/Application\ Support/Sublime\ Text\ 3/Packages/NodeRequirer`

#### Linux
`git clone https://github.com/ganemone/NodeRequirer.git ~/.config/sublime-text-3/Packages/NodeRequirer`

#### Windows
`git clone https://github.com/ganemone/NodeRequirer.git "%APPDATA%/Sublime Text 3/Packages/NodeRequirer"`
