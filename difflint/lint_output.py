# Copyright 2015 Endless Mobile, Inc.

import subprocess


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
        """Run the given linter command and capture its output and exit
        code."""
        try:
            output_bytes = subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            output_bytes = e.output
            self._warnings_present = True
        self.output += output_bytes.decode()
