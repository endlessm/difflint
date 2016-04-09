import argparse
import datetime
import difflib
import io
import os
import os.path
import pathlib
import re
import subprocess
import sys

from .lint import get_missing_configuration_files, get_missing_linters, lint
from .utils import repo_root

LOG_FILE = 'lintdiff.log'
MISSING_FILE_EXIT_CODE = 72  # os.EX_OSFILE is not portable

def lint_list(file_list):
    """Lint every file in the list with a linter appropriate to its extension.

    If no linter exists for that file type, this function will ignore that file.

    Input: file_list: A list of filenames containing no duplicates.

    Output: A mapping of filenames to their linted output as a LintOutput
            object.
    """
    return {f: lint(f) for f in file_list}

def build_rename_dict():
    """Build a dictonary of the new filenames of renamed files.

    Returns a dictionary mapping files' original names to the new filenames they
    are being changed to.

    Input: (none)
    Output: A dictionary of the form {new_name : old_name}
    """
    git_diff_output = subprocess.check_output(['git', 'diff', '--name-status',
                                               '--staged', '--find-renames',
                                               '--diff-filter=R'])
    # Has the format:
    #
    # R<NUM> <old-name> <new-name>
    #
    # where <NUM> is the similarity index between those two
    # files.

    rename_lines = list(git_diff_output.decode().split('\n'))
    new_to_old = {}
    for line in rename_lines:
        if line == '':
            break
        line_as_list = line.split('\t')
        new_to_old[line_as_list[2]] = line_as_list[1]
    return new_to_old

def build_file_list(mode_string):
    """Build a list of staged files matching certain diff-filter statuses.

    Returns a list containing the files matching the qualities
    indicated by the mode_string within the current git staging
    area.

    Input: mode_string: A string of git diff-filter statuses. Multiple statuses
           are allowed in any order; simply concatenate the statuses
           together. Examples: 'A' indicates added. 'CM' indicates
           copied or modified (set union not intersection).

    Output: A list of filenames that matched the git diff-filter
            criteria.
    """
    git_diff_output = subprocess.check_output(['git', 'diff', '--name-only',
                                               '--staged', '--find-renames',
                                               '--diff-filter=' + mode_string])
    return list(git_diff_output.decode().split())

def get_log_header():
    """Get a human-readable string header for the log file."""
    return str(datetime.datetime.utcnow().isoformat(' ')) + '\n'

def diff_lint_outputs(past_mapping, current_mapping, log_output,
                      rename_mapping={}):
    """Diff the linter outputs from two different dictionaries of files.

    Outputs with the same keys will be compared. The logging details will be
    output to a StringIO object, called log_output.

    Input:
        past_mapping: Dictionary of the form
            {filename, LintOutput}
        current_mapping: Dictionary of the form
            {filename, LintOutput}
        log_output: StringIO object to receive logging messages if
            new linting warnings/errors were introduced.
        rename_mapping: (optional) Dictionary of the form
            {new_filename : old_filename}

    Output: None
    """
    for new_name, lint_output in current_mapping.items():
        old_name = rename_mapping.get(new_name, new_name)
        if current_mapping[new_name] == past_mapping[old_name]:
            continue
        old_strings = past_mapping[old_name].get_split_output()
        new_strings = current_mapping[new_name].get_split_output()
        delta_generator = difflib.unified_diff(old_strings, new_strings,
                                               fromfile=old_name,
                                               tofile=new_name,
                                               n=0)  # No lines of context
        log_output.write('\n\n\n')
        log_output.writelines(delta_generator)

def report_defects_in_new_files(added_mapping, log_output):
    """Check LintOutput objects for the presence of warnings.

    Checks the given dictionary for any warning_booleans that have
    been set. If any are found, their corresponding linting output
    will be reported to the log_output.

    Inputs:
        added_mapping: Dictionary of the form
            {filename, LintOutput}
        log_output: StringIO object to receive logging messages if
            new linting warnings/errors were introduced.

    Output:
        True if warnings or errors were introduced; False otherwise.
    """
    any_errors_introduced = False
    for filename, lint_output in added_mapping.items():
        if not lint_output.has_warnings():
            continue
        any_errors_introduced = True
        log_output.write('\n\n\n')
        log_output.write(filename + '\n')
        log_output.write(lint_output.output)
    return any_errors_introduced

def finalize_log_output(log_output, any_new_errors):
    """Write the log to disk and print a message if there was something in it.

    Writes the contents of the log_output to the LOG_FILE and
    prints a notice to stderr if any_new_errors is True. Deletes
    any existing LOG_FILE if any_new_errors is False.

    Inputs:
        log_output: A StringIO of linting warnings/errors.
        any_new_errors: A boolean indicating whether any
                        errors were introduced.
    Outputs: None
    """
    if not any_new_errors:
        try:
            os.unlink(LOG_FILE)
        except FileNotFoundError:
            pass
    else:
        sys.stderr.write('NOTICE: Check ' + LOG_FILE +
                         ' for linting error details.\n')
        with open(LOG_FILE, 'w') as f:
            f.write(get_log_header())
            f.write(log_output.getvalue())
    log_output.close()

def detect_new_diff_lint_errors(log_output):
    """Determine whether a linting diff indicates new errors.

    Reads the diff of the linting outputs stored in log_output to see if it
    indicates the introduction of any new errors.

    Input: StringIO object containing the outputs of a diff
           tool applied to the linting output.

    Output: True if newly introduced errors are found; False
            otherwise.
    """
    output_by_lines = log_output.getvalue().split('\n')

    # Regex explanation:
    # - Starts with a character that isn't a minus.
    #   (This is either the start of the filename,
    #   an entire one-character filename or a +
    #   indicating a new error in a modified file.)
    #
    # - Followed by zero or more non-newline characters.
    #   (This is either the entire filename, the
    #   remainder of the filename, or nothing.)
    #
    # - Followed by a | literal
    # - Followed by one or more non-newline characters
    #   (This is the error's name.)
    #
    # - Followed by another | literal
    # - Followed by one or more non-newline characters
    #   (This is the error's description.)
    error_regex = re.compile(r'^[^\-].*\|.+\|.+')

    for output_line in output_by_lines:
        if error_regex.match(output_line):
            return True
    return False

def save_merge_state():
    """Saves the merge state in the event that we're resolving a
    merge conflict. Stashing will mangle the merge state unless
    we have saved it ahead of time. The reverse operation to this
    function is restore_merge_state().

    Special thanks to the overcommit project for solving this
    problem in a similar context. (https://github.com/brigade/overcommit)

    Inputs: None

    Output: If we were in a merge conflict state, this will return a
            tuple containing first the merge message, and second the
            merge commit hash.
            If we were not in a merge conflict state, this will return a
            tuple containing first an empty string, and second another
            empty string.
    """
    merge_head_commit_hash = ''
    try:
        # This will fail if MERGE_HEAD doesn't exist.
        merge_head_commit_hash = \
            subprocess.check_output(['git', 'rev-parse', 'MERGE_HEAD'],
                                    stderr=subprocess.DEVNULL).decode()
    except subprocess.CalledProcessError:
        return ('', '')

    merge_msg = ''

    merge_msg_path = repo_root() / '.git' / 'MERGE_MSG'
    if merge_msg_path.is_file():
        merge_msg = merge_msg_path.read_text()

    return (merge_msg, merge_head_commit_hash)

def restore_merge_state(merge_msg, merge_head_commit_hash):
    """Restores the merge state saved by a previous call to
    save_merge_state(). This function should only be called
    if save_merge_state() returned a non-empty string.

    Inputs:
        merge_msg: The saved message from a merge conflict

        merge_head_commit_hash: The hash belonging to the
            MERGE_HEAD reference.

    Output: None
    """
    dot_git = repo_root() / '.git'
    (dot_git / 'MERGE_MODE').touch(exist_ok=True)
    (dot_git / 'MERGE_HEAD').write_text(merge_head_commit_hash)
    (dot_git / 'MERGE_MSG').write_text(merge_msg + '\n')

def main():
    parser = argparse.ArgumentParser(description='Linter that will examine ' +
                                     'only new changes as you commit them.')
    parser.add_argument('-c', '--check', action='store_true',
                        help='Checks to see if all linting tools are in the ' +
                        'PATH. If some are missing, reports which ones.')
    args = parser.parse_args()

    missing_configurations = get_missing_configuration_files()
    
    missing_linters = []

    # We cannot find the missing_linters if any required configuration files
    # are missing.
    if not missing_configurations:
        missing_linters = get_missing_linters()

    if args.check:
        if not missing_linters and not missing_configurations:
            print('All configuration files and linting programs found.')
            return 0
        for linter_dict in missing_linters:
            print('Linter "' + linter_dict['linter'] + ' for the language "' +
                  linter_dict['language'] + '" is enabled but not found.')
        for missing_configuration in missing_configurations:
            print('Configuration file "' + missing_configuration + '"' +
                  ' is missing.')
        return MISSING_FILE_EXIT_CODE
    
    if missing_configurations:
        sys.stderr.write('Required configuration files missing. ' +
                         'Run `difflint --check` for a list of missing ' +
                         'configuration files.\n')
        return 0

    if missing_linters:
        sys.stderr.write('Required linting files missing. ' +
                         'Run `difflint --check` for a list of missing ' +
                         'files.\n')
        return 0

    all_staged_files = build_file_list('ACMR')
    if not all_staged_files:
        # No need to lint any files.
        return 0

    # Save any state related to merge conflicts because we will lose them
    # once we perform any git stashing.
    merge_msg, merge_hash = save_merge_state()

    # Put all changes made that *are not* being committed in the stash.
    subprocess.call(['git', 'stash', 'save', '--keep-index', '--quiet',
                     '"pre-commit hook unstaged changes"'])

    # Build a dictionary containing the filenames of copied and modified
    # files mapped to the output obtained from linting them.
    changed_file_list = build_file_list('CM')
    current_modified_lint_mapping = lint_list(changed_file_list)

    # Build a dictionary containing the filenames of added files mapped
    # to the output obtained from linting them.
    added_file_list = build_file_list('A')
    added_lint_mapping = lint_list(added_file_list)

    # Build a dictionary containing the new filenames of renamed files
    # mapped to the output obtained from linting them.
    current_renamed_file_list = build_file_list('R')
    current_renamed_lint_mapping = lint_list(current_renamed_file_list)

    # We also need a list of the old filenames that the renamed files
    # have been derived from.
    new_to_old_rename_mapping = build_rename_dict()

    # Now, we'll roll back changes that *are* being committed as well to
    # get the baseline linting output.
    subprocess.call(['git', 'stash', 'save', '--quiet',
                     '"pre-commit hook staged changes"'])

    # We only lint the files that existed in the past and the present.
    # (We don't try to lint files that were deleted or added in the
    # present.)
    past_modified_lint_mapping = lint_list(changed_file_list)

    old_names_list = list(new_to_old_rename_mapping.values())
    past_renamed_lint_mapping = lint_list(old_names_list)

    # Restore the changes that WILL NOT be committed first.
    subprocess.call(['git', 'stash', 'apply', '--index', '--quiet',
                     'stash@{1}'])

    # Restore the changes that WILL be committed now.
    subprocess.call(['git', 'stash', 'apply', '--index', '--quiet',
                     'stash@{0}'])

    # Remove both stash frames.
    subprocess.call(['git', 'stash', 'drop', '--quiet'])
    subprocess.call(['git', 'stash', 'drop', '--quiet'])

    # If the output from our save_merge_state wasn't an empty string,
    # we need to load the merge conflict state.
    if merge_hash:
        restore_merge_state(merge_msg, merge_hash)

    # Compare the two linting output dictionaries of copied/modified files.
    log_output = io.StringIO()
    diff_lint_outputs(past_modified_lint_mapping,
                      current_modified_lint_mapping, log_output)

    # Check each added file for defects.
    added_new_errors = report_defects_in_new_files(added_lint_mapping,
                                                   log_output)

    # Compare the linting outputs of the renamed files.
    diff_lint_outputs(past_renamed_lint_mapping,
                      current_renamed_lint_mapping, log_output,
                      new_to_old_rename_mapping)

    new_diff_lint_errors = detect_new_diff_lint_errors(log_output)
    any_new_errors = added_new_errors or new_diff_lint_errors
    finalize_log_output(log_output, any_new_errors)

    # This is where we could accept or reject commits via return code.
    return 0
