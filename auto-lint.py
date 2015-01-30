#!/usr/bin/env python3

from datetime import datetime
from difflib import unified_diff
from io import StringIO
from os import getcwd, listdir, unlink
from os.path import exists, isfile, join, splitext
from subprocess import call, check_output
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
             output.
    '''
    # Mapping of {filename : linting output}
    lint_mapping = {}

    for f in file_list:
        root, ext = splitext(f)
        if ext == ".js":
            lint_output = check_output(["/usr/bin/lint.sh", f])
            lint_mapping[f] = lint_output.decode()
        # TODO: Other file extensions/linters will be added here.

    return lint_mapping

def main():
    if not exists(LINT_PATH):
        stderr.write("No lint script found at '" + LINT_PATH + "'!\n")
        return

    # Put all changes made that *are not* being committed in the stash.
    call(["git", "stash", "save", "--keep-index", "--quiet",
          '"pre-commit hook unstaged changes"'])

    changed_file_output = check_output(["git", "diff", "--name-only",
                                        "--staged", "--diff-filter=CM"])
    changed_file_list = list(map(bytes.decode, changed_file_output.split()))
    current_lint_mapping = lint_list(changed_file_list)

    # Now, we'll roll back changes that *are* being committed as well to
    # get the baseline linting output.
    call(["git", "stash", "save", "--quiet",
          '"pre-commit hook staged changes"'])

    past_lint_mapping = lint_list(changed_file_list)

    # Restore the changes that WILL NOT be committed first.
    call(["git", "stash", "apply", "--index", "--quiet", "stash@{1}"])

    # Restore the changes that WILL be committed now.
    call(["git", "stash", "apply", "--index", "--quiet", "stash@{0}"])

    # Remove both stash frames.
    call(["git", "stash", "drop", "--quiet"])
    call(["git", "stash", "drop", "--quiet"])

    # Compare the two linting output dictionaries.
    any_errors_introduced = False
    diff_output = StringIO()
    for filename, output in current_lint_mapping.items():
        if current_lint_mapping[filename] == past_lint_mapping[filename]:
            print("Changes to " + filename + " introduced no new linting " +
                  "errors.")
            continue
        # If this is the first error, start the LOG_FILE with a timestamp.
        if not any_errors_introduced:
            any_errors_introduced = True
            diff_output.write(str(datetime.utcnow().isoformat(" ")) + "\n")
                
        print("WARNING: Changes to " + filename + " introduced linting errors!")

        old_strings = past_lint_mapping[filename].splitlines(keepends=True)
        new_strings = current_lint_mapping[filename].splitlines(keepends=True)
        delta_generator = unified_diff(old_strings, new_strings,
                                       fromfile=filename, tofile=filename,
                                       n=0) # No lines of context
        
        diff_output.write("\n\n\n")
        diff_output.writelines(delta_generator)

    # We shouldn't even have a log file if no new errors were introduced.
    if not any_errors_introduced:
        try:
            unlink(LOG_FILE)
        except FileNotFoundError:
            pass
    else:
        print("NOTICE: Check " + LOG_FILE + " for linting error details.")
        with open(LOG_FILE, 'w') as f:
            f.write(diff_output.getvalue())
    diff_output.close()

    # TODO: Accept/Reject based upon diffs matching or not.

if __name__ == "__main__":
    main()
