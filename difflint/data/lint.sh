#!/bin/bash

usage()
{
    cat <<EOF
Usage:  $0 FILE [MODE]
  or:   $0 -h
Unless the -h option is given, this script performs linting on the given FILE
according to its file extension. If multiple styles or languages are possible
with a given extension, an optional MODE may be given to specify which linting
tools and style rules will be used for that file.

    Currently Supported MODEs:

    gjs : GNOME JavaScript -- default
    node : Node.js
    web : browser JavaScript

    Options:

    --help, -h : Display this usage information and exit.

    Exit Codes:

    0 : No errors.
    1 : Linting errors found.
    2 : The script has configuration errors or invalid usage.
EOF
}

file_to_lint="$1"
mode="$2"
ret=0

JSCS_REPORTER=`python3 -c 'print(__import__("pkg_resources").resource_filename("difflint", "data/jscs_terse_reporter.js"))'`
JSHINT_REPORTER=`python3 -c 'print(__import__("pkg_resources").resource_filename("difflint", "data/jshint_terse_reporter.js"))'`

NODE_JSHINTRC=`python3 -c 'print(__import__("pkg_resources").resource_filename("difflint", "data/node.jshintrc"))'`
WEB_JSHINTRC=`python3 -c 'print(__import__("pkg_resources").resource_filename("difflint", "data/web.jshintrc"))'`

if [[ "$#" == 0 ]]
  then
    usage
    exit 2
fi

if [ "$1" == "-h" -o "$1" == "--help" ]
  then
    usage
    exit 0
fi

jscs "$file_to_lint" --reporter="$JSCS_REPORTER" || ret=$?

if [ "$mode" == "node" -o "$mode" == "nodejs" ]
  then
    jshint "$file_to_lint" --reporter="$JSHINT_REPORTER" --config="$NODE_JSHINTRC" || ret=$?
elif [ "$mode" == "web" -o "$mode" == "webjs" ]
  then
    jshint "$file_to_lint" --reporter="$JSHINT_REPORTER" --config="$WEB_JSHINTRC" || ret=$?
else
    jshint "$file_to_lint" --reporter="$JSHINT_REPORTER" || ret=$?
fi

exit $ret
