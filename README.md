# Difflint #

Suppose you have a codebase with inconsistent code style, and you want
to start checking your commits with a linter.
You could fix the entire thing in one gargantuan code style commit, but
you might not want to do that if you rely on your commit history for
tracking down bugs with tools like `git blame` and `git bisect`.

**Difflint** will check only the changes that you make in each commit.
It's suitable for using as a Git pre-commit hook.

## Linters Supported ##

- [ESLint](http://eslint.org) (Javascript)
- [JSCS](http://jscs.info) (JavaScript -- Default)
- [JSHint](http://jshint.com/docs) (JavaScript -- Default)
- [PEP8](https://pypi.python.org/pypi/pep8) (Python -- Default)
- [PyFlakes](https://pypi.python.org/pypi/pyflakes) (Python -- Default)

## Requirements ##

- Python 3.5 or later
- NPM for installing default Javascript linters
- JSCS (Installed/Enabled by default)
- JSHint (Installed/Enabled by default)

## Installation ##

- Clone this repository, and run `python3 setup.py install`.
- Install Difflint as a pre-commit hook by adding a line saying
  `difflint` to `.git/hooks/pre-commit` in the project that you want to
  lint.
  (Create the `.git/hooks/pre-commit` file if it doesn't exist.
  For Windows add `#!/bin/sh` first.)
  _You can set this up automatically for new git clones by putting it in
  your [Git template](http://git-scm.com/docs/git-init)._
- Install JSCS and JSHint with `npm install -g jscs` and `npm install -g jshint`.

## Usage ##

Use `difflint -c` to make sure that Difflint can find all the linting
tools it needs.

Whenever you make a commit in a Git repository where you've installed
Difflint as a pre-commit hook, Difflint will check the lines you're
about to commit and warn you if you've added any new errors that weren't
already there.

You can check without committing by staging the files you wish to check
(with `git add`) and running `difflint` without any arguments.

## Enable/Disable Linters (optional) ##

Difflint allows you to specify which linters to use for particular
file extensions. Any linters included in the section "Linters Supported"
can be enabled or disabled. You can configure this by renaming the
example.difflintrc file to .difflintrc and placing it in your repository's
root level. Then you can change which file extensions belong to which
groups of linters, disable some of the default linters, or add other
linters that are not enabled by default.

If you do not supply a .difflintrc file, default values for extensions
and linters will be used. They can be found in the [default difflintrc file](difflint/data/.difflintrc).

The format of the .difflintrc file is JSON and looks like the following:

```js
{
    "<language_name>": {
        "extensions": ["<file_extension_without_a_leading_dot_1>",
                       "<file_extension_without_a_leading_dot_2>"],
        "linters": ["<linter_executable_name_1>",
                    "<linter_executable_name_2>"]
    }
}
```

Here the `<language_name>` could be something like "python" or "javascript".
It is not used in the linting process but will help generate useful error
messages if you forgot to install one of the linters you associated with it.

The `<file_extension_without_a_leading_dot>` could be "py" or "pyw". Example
linter executable names are "pep8" and "jscs". You are free to mix and match
groupings/extensions/linters as best fits your workflow.

## Linter Specific Configuration (optional) ##

If you don't want JSCS and JSHint's default settings, create `.jscsrc`
and `.jshintrc` files where JSCS and JSHint can find them.
We've created example ones in this repository, named `example.jscsrc`
and `example.jshintrc` that you can rename and customize.
See [JSCS documentation](http://jscs.info/overview) and [JSHint
documentation](http://jshint.com/docs/) for more information.

## Bug Reporting ##

Report bugs using Difflint's [issue tracking on Github](https://github.com/endlessm/difflint/issues).
