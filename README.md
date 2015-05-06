# NodeRequirer - A Sublime Text 3 plugin for requiring node modules
#### [Sublime Text 3](http://www.sublimetext.com/3)

## About
This is a Sublime Text 3 plugin allowing you to easily require node modules
without having to worry about relative paths. It parses your project to allow you
to require any local module or dependency listed in your package.json. In addition, it allows
you to include node core modules.

## Usage
`ctrl+shift+i` => `RequireCommand`

Provides a dropdown of local files, node core modules, and dependencies defined in package.json + bower.json
SublimeRequirer will insert `var {modulename} = require('/path/to/modulename.js')`.

Example:
```javascript
var Person = require('../../models/person.js');
var MovieStar = require('../../movie-star.js');
```

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
## Options

`NodeRequirer` exposes several useful plugin options for configuring aliases, import modes and quotes. These are available under `Preferences -> Package Settings -> Node Require` or search for `NodeRequirer: Set plugin options`

Example `User Plugin Preferences`

```javascript
{
    // Type of quotes to use
    "quotes": "single || double",
    
    // Use ES6 import format, when syntactically correct
    "import": false,
    
    "alias": {
        // <module name>: <variable name>
        "underscore": "_"
    }
    
    // Use object destructuring when assigning multiple exports 
    "destructuring": false,
    
    // Use snippets when inserting require statements to allow
    // for easy variable name changing
    "snippet": true
}
```

## Installation
### Through [Sublime Package Manager](http://wbond.net/sublime_packages/package_control)

* `Ctrl+Shift+P` or `Cmd+Shift+P` in Linux/Windows/OS X
* type `install`, select `Package Control: Install Package`
* type `NodeRequirer`, select `NodeRequirer`

IMPORTANT: In order for node-requirer to parse your project correctly, you must have a
.sublime-project file configured with the absolute path to your project. To create this file,
select Project => Save Project As => and name your .sublime-project file what ever you want.
Trying to require a file before this file has been created will prompt the user for a path, 
using the directory of the current file as default, and automatically create the file for you.
Then edit the file to include a key called "path" with a value being the absolute path to your projects
root directory.

Example:
```javascript
{
  "folders":
  [
    {
      "follow_symlinks": true,
      "path": "/Users/giancarloanemone/Documents/dev/node/projectname"
    }
  ]
}
```

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
