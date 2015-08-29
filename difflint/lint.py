# Copyright 2015 Endless Mobile, Inc.

import os.path
from pkg_resources import resource_filename
import shutil

from .lint_output import LintOutput
from .lint_python import PythonLintOutput


def get_missing_linters():
    """Check that all required external executables are in the PATH.

    Output: a list of executables that are not found, or an empty list if
    everything is OK.
    """
    REQUIRED = ('jscs', 'jshint')
    return [cmd for cmd in REQUIRED if shutil.which(cmd) is None]


def _lint_javascript(file_to_lint):
    output = LintOutput()
    jscs = shutil.which('jscs')
    output.run_command([jscs, file_to_lint, '--reporter',
                        resource_filename(__name__,
                                          'data/jscs_terse_reporter.js')])

    jshint = shutil.which('jshint')
    output.run_command([jshint, file_to_lint, '--reporter',
                        resource_filename(__name__,
                                          'data/jshint_terse_reporter.js')])
    return output


def _lint_python(file_to_lint):
    output = PythonLintOutput()
    output.lint_pep8(file_to_lint)
    output.lint_pyflakes(file_to_lint)
    return output


def lint(file_to_lint):
    """Perform linting on a file according to its extension.

    Inputs:
        file_to_lint: Path to a file to lint, as a string.
    Output: A LintOutput object with linting results.
    """
    root, ext = os.path.splitext(file_to_lint)

    if ext == '.js':
        return _lint_javascript(file_to_lint)
    if ext == '.py':
        return _lint_python(file_to_lint)

    # TODO: Other file extensions/linters will be added here.
