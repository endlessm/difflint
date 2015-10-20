# Copyright 2015 Endless Mobile, Inc.

import os.path
from pkg_resources import resource_filename
import shutil
import subprocess


def get_missing_linters():
    """Check that all required external executables are in the PATH.

    Output: a list of executables that are not found, or an empty list if
    everything is OK.
    """
    REQUIRED = ('jscs', 'jshint')
    return [cmd for cmd in REQUIRED if shutil.which(cmd) is None]


class LintOutput(object):
    """Encapsulate linter output from multiple linters."""

    def __init__(self):
        self.output = ''
        self._warnings_present = False

    def has_warnings(self):
        """Return whether any linters indicated errors or warnings."""
        return self._warnings_present

    def get_split_output(self):
        """Return the linter output as an array of strings."""
        return self.output.splitlines(keepends=True)

    def run_command(self, args):
        """Run the given linter command and capture its output and exit code."""
        try:
            output_bytes = subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            output_bytes = e.output
            self._warnings_present = True
        self.output += output_bytes.decode()


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


def lint(file_to_lint):
    """Perform linting on a file according to its extension.

    Inputs:
        file_to_lint: Path to a file to lint, as a string.
    Output: A LintOutput object with linting results.
    """
    root, ext = os.path.splitext(file_to_lint)

    if ext == '.js':
        return _lint_javascript(file_to_lint)

    # TODO: Other file extensions/linters will be added here.