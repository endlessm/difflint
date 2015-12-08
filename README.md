# Difflint #

Suppose you have a codebase with inconsistent code style, and you want
to start checking your commits with a linter.
You could fix the entire thing in one gargantuan code style commit, but
you might not want to do that if you rely on your commit history for
tracking down bugs with tools like `git blame` and `git bisect`.

**Difflint** will check only the changes that you make in each commit.
It's suitable for using as a Git pre-commit hook.

## Linters supported ##

- [JSCS](http://jscs.info) (JavaScript)
- [JSHint](http://jshint.com/docs) (JavaScript)
- [PEP8](https://pypi.python.org/pypi/pep8) (Python)
- [PyFlakes](https://pypi.python.org/pypi/pyflakes) (Python)

## Requirements ##

- Python 3.3 or later
- JSCS
- JSHint
- NPM for installing JSCS and JSHint

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

## Configuration (optional) ##

If you don't want JSCS and JSHint's default settings, create `.jscsrc`
and `.jshintrc` files where JSCS and JSHint can find them.
We've created example ones in this repository, named `example.jscsrc`
and `example.jshintrc` that you can rename and customize.
See [JSCS documentation](http://jscs.info/overview) and [JSHint
documentation](http://jshint.com/docs/) for more information.

## Bug Reporting ##

Report bugs using Difflint's [issue tracking on Github](https://github.com/endlessm/difflint/issues).
