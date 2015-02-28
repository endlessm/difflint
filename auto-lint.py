#!/usr/bin/env python3

from datetime import datetime
from difflib import unified_diff
from io import StringIO
from os import getcwd, listdir, unlink
from os.path import exists, isfile, join, splitext
from subprocess import call, check_output, CalledProcessError
from sys import stderr

LOG_FILE = "lintdiff.log"
LINT_PATH = "/usr/bin/lint.sh"

def lint_list(file_list):
    '''
    Lints every file within file list with a linter
    appropriate to its extension. If no linter exists
    for that file type, this function will ignore that
    file.

    Input: A list of filenames containing no duplicates.

    Returns: A mapping of filenames to their linted
             output and whether or not there were any
             warnings.
    '''
    # Mapping of {filename : [linting output, warnings boolean]}
    lint_mapping = {}

    for f in file_list:
        root, ext = splitext(f)
        if ext == ".js":
            lint_output = None
            warnings_present = False
            try:
                lint_output = check_output([LINT_PATH, f])
            except CalledProcessError as e:
                warnings_present = True
                lint_output = e.output
            lint_mapping[f] = [lint_output.decode(), warnings_present]
        # TODO: Other file extensions/linters will be added here.

    return lint_mapping

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
                                    "--staged",
                                    "--diff-filter=" + mode_string])
    return list(git_diff_output.decode().split())

def main():
    if not exists(LINT_PATH):
        stderr.write("No lint script found at '" + LINT_PATH + "'!\n")
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

    # Now, we'll roll back changes that *are* being committed as well to
    # get the baseline linting output.
    call(["git", "stash", "save", "--quiet",
          '"pre-commit hook staged changes"'])

    # We only lint the files that existed in the past and the present.
    # (We don't try to lint files that were deleted or added in the
    # present.)
    past_modified_lint_mapping = lint_list(changed_file_list)

    # Restore the changes that WILL NOT be committed first.
    call(["git", "stash", "apply", "--index", "--quiet", "stash@{1}"])

    # Restore the changes that WILL be committed now.
    call(["git", "stash", "apply", "--index", "--quiet", "stash@{0}"])

    # Remove both stash frames.
    call(["git", "stash", "drop", "--quiet"])
    call(["git", "stash", "drop", "--quiet"])

    # Compare the two linting output dictionaries of copied/modified files.
    any_errors_introduced = False
    log_output = StringIO()
    for filename, output in current_modified_lint_mapping.items():
        if current_modified_lint_mapping[filename] == past_modified_lint_mapping[filename]:
            print("Changes to " + filename + " introduced no new linting " +
                  "errors.")
            continue
        # If this is the first error, start the LOG_FILE with a timestamp.
        if not any_errors_introduced:
            any_errors_introduced = True
            log_output.write(str(datetime.utcnow().isoformat(" ")) + "\n")
                
        print("WARNING: Changes to " + filename + " introduced linting errors!")

        old_strings = past_modified_lint_mapping[filename][0].splitlines(keepends=True)
        new_strings = current_modified_lint_mapping[filename][0].splitlines(keepends=True)
        delta_generator = unified_diff(old_strings, new_strings,
                                       fromfile=filename, tofile=filename,
                                       n=0) # No lines of context
        
        log_output.write("\n\n\n")
        log_output.writelines(delta_generator)

    # Check each added file for defects.
    for filename, output in added_lint_mapping.items():
        if not output[1]:
            #output[1] tells us whether any warnings exist.
            continue
        if not any_errors_introduced:
            # Note, this duplicate code will be removed when we go to
            # single line reporting.
            any_errors_introduced = True
            log_output.write(str(datetime.utcnow().isoformat(" ")) + "\n")

        print("WARNING: New file " + filename + " has linting errors!")
        log_output.write("\n\n\n")
        log_output.write(filename + "\n")
        log_output.write(output[0])

    # We shouldn't even have a log file if no new errors were introduced.
    if not any_errors_introduced:
        try:
            unlink(LOG_FILE)
        except FileNotFoundError:
            pass
    else:
        print("NOTICE: Check " + LOG_FILE + " for linting error details.")
        with open(LOG_FILE, 'w') as f:
            f.write(log_output.getvalue())
    log_output.close()

    # TODO: Accept/Reject based upon diffs matching or not.

if __name__ == "__main__":
    main()
