# Copyright 2015 Endless Mobile, Inc.

import pep8


# We could do this with pep8.StandardReport and its format parameter directly,
# but it prints to stdout by default. We don't want that.
class PEP8TerseReporter(pep8.BaseReport):
    """Prints the PEP8 linter results in the expected "terse" format."""

    def __init__(self):
        super(PEP8TerseReporter, self).__init__(pep8.StyleGuide().options)
        self.output = ''

    def error(self, line_number, offset, text, check):
        code = super(PEP8TerseReporter, self).error(line_number, offset, text,
                                                    check)
        self.output += '{}|{}|{}\n'.format(self.filename, code, text)
        return code


class PyFlakesTerseReporter:
    """A very minimal reimplementation of PyFlakes' Reporter class, changed
    to print messages in the expected "terse" format. See:
    https://github.com/pyflakes/pyflakes/blob/master/pyflakes/reporter.py
    """

    def __init__(self):
        super(PyFlakesTerseReporter, self).__init__()
        self.output = ''

    def unexpectedError(self, filename, msg):
        self.output += '{}|FATAL|{}'.format(filename, msg)

    def syntaxError(self, filename, msg, lineno, offset, text):
        self.output += '{}|SYNTAX|{}'.format(filename, msg)

    def flake(self, message):
        message_text = message.message % message.message_args
        self.output += '{}|FLAKE|{}'.format(message.filename, message_text)
