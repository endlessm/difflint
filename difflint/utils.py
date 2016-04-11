# TODO License goes here. (MIT)

import functools
import pathlib

@functools.lru_cache()
def repo_root():
    """Returns the root of the current repository. This is the directory
    containing the .git directory for this repository.

    Input: None

    Output: A pathlib.Path object representing the root of this repository.
    """
    directory = pathlib.Path.cwd()
    while directory.parent != directory.root:
        if (directory / '.git').is_dir():
            return directory
        directory = directory.parent

    raise FileNotFoundError("Could not find .git folder in any ancestor" +
                            " directory.")
