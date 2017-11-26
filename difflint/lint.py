# Copyright 2015 Endless Mobile, Inc.

import functools
import json
import os.path
import pathlib
import pep8
from pkg_resources import resource_filename
import pyflakes.api
import shutil
import sys

from .lint_output import LintOutput
from .python_reporters import PEP8TerseReporter, PyFlakesTerseReporter
from .utils import repo_root

@functools.lru_cache()
def _get_enabled_linters_config_path():
    """Returns the path of the file describing which linters are enabled
    based upon whether a custom, repository-specific file exists.

    Inputs: None

    Output: A patlib.Path object.
    """
    custom_path = repo_root() / '.difflintrc'
    if custom_path.is_file():
        return custom_path
    return pathlib.Path(resource_filename(__name__, 'data/.difflintrc'))

@functools.lru_cache()
def _read_enabled_linters_config():
    """Reads from the configuration file to determine which linters
    should be used for which file extensions. This will first attempt
    to read from a custom configuration file specific to the current
    repository. If it cannot find one, it will fall back on the
    default. If the custom file is not valid JSON, this will raise
    an exception.

    Inputs: None

    Output: A dictionary of languages mapped to a dictionary of extensions 
            and linters.

    Example Output Format:

    {
        "javascript": {
            "extensions": ["js"],
            "linters": ["jscs", "jshint"]
        },
        "python": {
            "extensions": ["py", "pyw"],
            "linters": ["pep8", "pyflakes"]
        }
    }
    """
    config_path = _get_enabled_linters_config_path()

    try:
        with config_path.open() as config:
            return json.load(config)
    except ValueError as ve:
        sys.stderr.write("Failed to parse custom .difflintrc file. " +
                         "Make sure the file is valid JSON or remove " +
                         "the file and fall back on the default " +
                         "configuration.\n")
        raise ve

def get_missing_configuration_files():
    """Check that all mandatory configuration files for difflint are
    in their expected locations.

    Inputs: None

    Output: A list of filepaths, as strings, of missing non-optional
            configuration files. Will return an empty list if all
            configuration files were found.
    """
    missing_configuration_files = []
    linter_enabled_config = _get_enabled_linters_config_path()
    if not linter_enabled_config.is_file():
        missing_configuration_files.append(linter_enabled_config)
    return missing_configuration_files

def get_missing_linters():
    """Check that all enabled linters' external executables (as defined in the 
    configuration file) are in the PATH.

    Inputs: None

    Output: A list containing dictionaries of the form:

                {'language': language, 'linter': linter_executable}

            if any linters are not found. Otherwise returns an empty list.
    """
    enabled_linters_dict = _read_enabled_linters_config()
    missing_linters = []
    for language, language_dict in enabled_linters_dict.items():
        for linter in language_dict['linters']:
            if shutil.which(linter) is None:
                missing_linters.append({'language': language,
                                        'linter': linter})
    return missing_linters

def _lint_eslint(file_to_lint, lint_output):
    eslint = shutil.which('eslint')
    lint_output.run_command([eslint, file_to_lint, '--format',
                             resource_filename(__name__,
                                               'data/eslint_terse_reporter.js')])
    return lint_output

def _lint_jscs(file_to_lint, lint_output):
    jscs = shutil.which('jscs')
    lint_output.run_command([jscs, file_to_lint, '--reporter',
                             resource_filename(__name__,
                                               'data/jscs_terse_reporter.js')])
    return lint_output

def _lint_jshint(file_to_lint, lint_output):
    jshint = shutil.which('jshint')
    lint_output.run_command([jshint, file_to_lint, '--reporter',
                             resource_filename(__name__,
                                               'data/jshint_terse_reporter.js')])
    return lint_output

def _lint_pep8(file_to_lint, lint_output):
    reporter = PEP8TerseReporter()
    checker = pep8.Checker(filename=file_to_lint, report=reporter)
    num_problems = checker.check_all()
    if num_problems > 0:
        lint_output._warnings_present = True
    lint_output.output += reporter.output
    return lint_output

def _lint_pyflakes(file_to_lint, lint_output):
    reporter = PyFlakesTerseReporter()
    num_problems = pyflakes.api.checkPath(file_to_lint, reporter=reporter)
    if num_problems > 0:
        lint_output._warnings_present = True
    lint_output.output += reporter.output
    return lint_output

def lint(file_to_lint):
    """Perform linting on a file according to its extension.

    Inputs: Path to a file to lint, as a string.

    Output: A LintOutput object with linting results.
    """
    root, ext = os.path.splitext(file_to_lint)

    # Strip the leading period to match the format in the configuration file.
    ext = ext[1:]

    # This value is cached across function calls, so it is not expensive to
    # continue reading this configuration for every file.
    config = _read_enabled_linters_config()

    linters_to_run = []
    for language, language_dict in config.items():
        if ext in language_dict['extensions']:
            linters_to_run.extend(language_dict['linters'])

    output = LintOutput()

    # Other file extensions/linters must be added here if they are to be used.
    for linter in linters_to_run:
        if linter == 'eslint':
            output = _lint_eslint(file_to_lint, output)
        elif linter == 'jshint':
            output = _lint_jshint(file_to_lint, output)
        elif linter == 'jscs':
            output = _lint_jscs(file_to_lint, output)
        elif linter == 'pep8':
            output = _lint_pep8(file_to_lint, output)
        elif linter == 'pyflakes':
            output = _lint_pyflakes(file_to_lint, output)
        else:
            raise ValueError('Unknown linter found in configuration file: "' +
                             linter + '"')
    return output
