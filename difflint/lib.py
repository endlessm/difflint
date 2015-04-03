from datetime import datetime
from difflib import unified_diff
from io import StringIO
from os import getcwd, listdir, unlink
from os.path import exists, isfile, join, splitext
from pkg_resources import resource_filename
import re
from subprocess import call, check_output, CalledProcessError
from sys import stderr

LOG_FILE = "lintdiff.log"
LINT_PATH = resource_filename(__name__, 'data/lint.sh')


class LintOutput(object):
    def __init__(self, output, warning_boolean):
        self.output = output
        self._warnings_present = warning_boolean # private
    
    def has_warnings(self):
        return self._warnings_present

    def get_split_output(self):
        return self.output.splitlines(keepends=True)


def lint_list(file_list):
    '''
    Lints every file within file list with a linter
    appropriate to its extension. If no linter exists
    for that file type, this function will ignore that
    file.

    Input: A list of filenames containing no duplicates.

    Returns: A mapping of filenames to their linted
             output as a LintOutput object.
    '''
    # Mapping of {filename : LintOutput}
    lint_mapping = {}

    for f in file_list:
        root, ext = splitext(f)
        if ext == ".js":
            lint_output_bytes = None
            warnings_present = False
            try:
                lint_output_bytes = check_output([LINT_PATH, f])
            except CalledProcessError as e:
                warnings_present = True
                lint_output_bytes = e.output
            lint_mapping[f] = LintOutput(lint_output_bytes.decode(),
                                         warnings_present)
        # TODO: Other file extensions/linters will be added here.

    return lint_mapping

def build_rename_dict():
    '''Builds a dictonary containing the new filenames renamed files
    are being changed to, mapped to their original names.

    Input: (none)
    Output: A dictionary of the form {new_name : old_name}
    '''
    git_diff_output = check_output(["git", "diff", "--name-status",
                                    "--staged", "--find-renames",
                                    "--diff-filter=R"])
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
        line_as_list = line.split("\t")
        new_to_old[line_as_list[2]] = line_as_list[1]
    return new_to_old

def build_file_list(mode_string):
    '''Builds a list containing the files matching the qualities
    indicated by the mode_string within the current git staging
    area.

    Input: A string of git diff-filter statuses. Multiple statuses
           are allowed in any order; simply concatenate the statuses
           together. Examples: 'A' indicates added. 'CM' indicates
           copied or modified (set union not intersection).

    Output: A list of filenames that matched the git diff-filter
            criteria.'''
    git_diff_output = check_output(["git", "diff", "--name-only",
                                    "--staged", "--find-renames",
                                    "--diff-filter=" + mode_string])
    return list(git_diff_output.decode().split())

def lint_script_exists():
    '''Checks to see if the file specified by LINT_PATH exists.
    Writes an error message to stderr and returns False if it
    does not. Otherwise returns True.'''
    if not exists(LINT_PATH):
        stderr.write("No lint script found at '" + LINT_PATH + "'!\n")
        return False
    return True

def get_log_header():
    '''Returns a string header to be used with the log file
    containing the current date in a readable format.'''
    return str(datetime.utcnow().isoformat(" ")) + "\n"

def diff_lint_outputs(past_mapping, current_mapping, log_output,
                      rename_mapping={}):
    '''Performs a diff of the linting outputs from two different
    dictionaries of files. Outputs with the same keys will be
    compared. The logging details will be output to a StringIO
    object, called log_output.

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
    '''
    for new_name, lint_output in current_mapping.items():
        old_name = rename_mapping.get(new_name, new_name)
        if current_mapping[new_name] == past_mapping[old_name]:
            continue
        old_strings = past_mapping[old_name].get_split_output()
        new_strings = current_mapping[new_name].get_split_output()
        delta_generator = unified_diff(old_strings, new_strings,
                                       fromfile=old_name, tofile=new_name,
                                       n=0) # No lines of context
        log_output.write("\n\n\n")
        log_output.writelines(delta_generator)

def report_defects_in_new_files(added_mapping, log_output):
    '''Checks the given dictionary for any warning_booleans that have
    been set. If any are found, their corresponding linting output
    will be reported to the log_output.

    Inputs:
        added_mapping: Dictionary of the form
            {filename, LintOutput}
        log_output: StringIO object to receive logging messages if
            new linting warnings/errors were introduced.

    Output:
        True if warnings or errors were introduced; False otherwise.
    '''
    any_errors_introduced = False
    for filename, lint_output in added_mapping.items():
        if not lint_output.has_warnings():
            continue
        any_errors_introduced = True
        log_output.write("\n\n\n")
        log_output.write(filename + "\n")
        log_output.write(lint_output.output)
    return any_errors_introduced

def finalize_log_output(log_output, any_new_errors):
    '''Writes the contents of the log_output to the LOG_FILE and
    prints a notice to stderr if any_new_errors is True. Deletes
    any existing LOG_FILE if any_new_errors is False.

    Inputs:
        log_output: A StringIO of linting warnings/errors.
        any_new_errors: A boolean indicating whether any
                        errors were introduced.
    Outputs: None'''
    if not any_new_errors:
        try:
            unlink(LOG_FILE)
        except FileNotFoundError:
            pass
    else:
        stderr.write("NOTICE: Check " + LOG_FILE +
                     " for linting error details.\n")
        with open(LOG_FILE, 'w') as f:
            f.write(get_log_header())
            f.write(log_output.getvalue())
    log_output.close()

def detect_new_diff_lint_errors(log_output):
    '''Determines if the diff of the linting outputs stored in
    log_output indicate the introduction of any new errors.

    Input: StringIO object containing the outputs of a diff
           tool applied to the linting output.

    Output: True if newly introduced errors are found; False
            otherwise.
    '''
    output_by_lines = log_output.getvalue().split("\n")

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
    error_regex = re.compile(r"^[^\-].*\|.+\|.+")

    for output_line in output_by_lines:
        if error_regex.match(output_line):
            return True
    return False

def main():
    if not lint_script_exists():
        return

    # Put all changes made that *are not* being committed in the stash.
    call(["git", "stash", "save", "--keep-index", "--quiet",
          '"pre-commit hook unstaged changes"'])

    # Build a dictionary containing the filenames of copied and modified
    # files mapped to the output obtained from linting them.
    changed_file_list = build_file_list("CM")
    current_modified_lint_mapping = lint_list(changed_file_list)

    # Build a dictionary containing the filenames of added files mapped
    # to the output obtained from linting them.
    added_file_list = build_file_list("A")
    added_lint_mapping = lint_list(added_file_list)

    # Build a dictionary containing the new filenames of renamed files
    # mapped to the output obtained from linting them.
    current_renamed_file_list = build_file_list("R")
    current_renamed_lint_mapping = lint_list(current_renamed_file_list)

    # We also need a list of the old filenames that the renamed files
    # have been derived from.
    new_to_old_rename_mapping = build_rename_dict()

    # Now, we'll roll back changes that *are* being committed as well to
    # get the baseline linting output.
    call(["git", "stash", "save", "--quiet",
          '"pre-commit hook staged changes"'])

    # We only lint the files that existed in the past and the present.
    # (We don't try to lint files that were deleted or added in the
    # present.)
    past_modified_lint_mapping = lint_list(changed_file_list)

    old_names_list = list(new_to_old_rename_mapping.values())
    past_renamed_lint_mapping = lint_list(old_names_list)

    # Restore the changes that WILL NOT be committed first.
    call(["git", "stash", "apply", "--index", "--quiet", "stash@{1}"])

    # Restore the changes that WILL be committed now.
    call(["git", "stash", "apply", "--index", "--quiet", "stash@{0}"])

    # Remove both stash frames.
    call(["git", "stash", "drop", "--quiet"])
    call(["git", "stash", "drop", "--quiet"])

    # Compare the two linting output dictionaries of copied/modified files.
    log_output = StringIO()
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

