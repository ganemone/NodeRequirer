# NodeRequirer - A Sublime Text 3 plugin for requiring node modules
#### [Sublime Text 3](http://www.sublimetext.com/3)

## About
This is a Sublime Text 3 plugin allowing you to easily require node modules
without having to worry about relative paths. It parses your project to allow you
to require any local module or dependency listed in your package.json. In addition, it allows
you to include node core modules.

## Usage
Simply type 'ctrl+shift+i' and search for the module you are looking to require.
SublimeRequirer will insert `var {modulename} = require('/path/to/modulename.js')`.

NOTE: I build sublime requirer to help me be more productive. Currently, it is configured to work well
with the naming convention that I use. For example, modules inside a /models folder will have their names
capitalized automatically. Additionally, any module with a name separated by dashes will remove the dash, and capitalize the individual words.

Example:
```
var Person = require('../../models/person.js');
var MovieStar = require('../../movie-star.js');
```

## Installation
### Through [Sublime Package Manager](http://wbond.net/sublime_packages/package_control)

* `Ctrl+Shift+P` or `Cmd+Shift+P` in Linux/Windows/OS X
* type `install`, select `Package Control: Install Package`
* type `NodeRequirer`, select `NodeRequirer`

IMPORTANT: In order for node-requirer to parse your project correctly, you must have a
.sublime-project file configured with the absolute path to your project. To create this file,
select Project => Save Project As => and name your .sublime-project file what ever you want.
Then edit the file to include a key called "path" with a value being the absolute path to your projects
root directory.

Example:
```
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

### Manually
Make sure you use the right Sublime Text folder. For example, on OS X, packages for version 2 are in `~/Library/Application\ Support/Sublime\ Text\ 2`, while version 3 is labeled `~/Library/Application\ Support/Sublime\ Text\ 3`.

These are for Sublime Text 3:

#### Mac
`git clone https://github.com/ganemone/NodeRequirer.git ~/Library/Application\ Support/Sublime\ Text\ 3/Packages/NodeRequirer`

#### Linux
`git clone https://github.com/ganemone/NodeRequirer.git ~/.config/sublime-text-3/Packages/NodeRequirer`

#### Windows
`git clone https://github.com/ganemone/NodeRequirer.git "%APPDATA%/Sublime Text 3/Packages/NodeRequirer"`



I will be making this more configurable in the future.

Thank you!
