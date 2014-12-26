#!/usr/bin/python3

from os import getcwd, listdir
from os.path import exists, isfile, join, splitext
from subprocess import call
from sys import stderr


def main():
    lint_path = "/usr/bin/lint.sh"
    if not exists(lint_path):
        stderr.write("No lint script found at '" + lint_path + "'!\n")
        return

    current_directory = getcwd()
    files = [f for f in listdir(current_directory) if
             isfile(join(current_directory, f))]
    for f in files:
        root, ext = splitext(f)
        if ext == ".py":
            print(f + " is a Python file.")
        elif ext == ".c":
            print(f + " is a C file.")
        elif ext == ".h":
            print(f + " is a C header file.")
        elif ext == ".js":
            print(f + " is a JavaScript file.")
            call(["/usr/bin/lint.sh", f])

if __name__ == "__main__":
    main()
