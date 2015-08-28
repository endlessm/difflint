# Copyright 2015 Endless Mobile, Inc.

import shutil


def get_missing_linters():
    """Check that all required external executables are in the PATH.

    Output: a list of executables that are not found, or an empty list if
    everything is OK.
    """
    REQUIRED = ('jscs', 'jshint')
    return [cmd for cmd in REQUIRED if shutil.which(cmd) is None]
