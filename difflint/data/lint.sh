#!/bin/bash

file_to_lint="$1"
mode="$2"
ret=0

JSCS_REPORTER=`python3 -c 'print(__import__("pkg_resources").resource_filename("difflint", "data/jscs_terse_reporter.js"))'`
JSHINT_REPORTER=`python3 -c 'print(__import__("pkg_resources").resource_filename("difflint", "data/jshint_terse_reporter.js"))'`

jscs "$file_to_lint" --reporter="$JSCS_REPORTER" || ret=$?

if [ "$mode" == "node" -o "$mode" == "nodejs" ]
  then
    NODE_JSHINTRC=`python3 -c 'print(__import__("pkg_resources").resource_filename("difflint", "data/node.jshintrc"))'`
    jshint "$file_to_lint" --reporter="$JSHINT_REPORTER" --config="$NODE_JSHINTRC" || ret=$?
elif [ "$mode" == "web" -o "$mode" == "webjs" ]
  then
    WEB_JSHINTRC=`python3 -c 'print(__import__("pkg_resources").resource_filename("difflint", "data/web.jshintrc"))'`
    jshint "$file_to_lint" --reporter="$JSHINT_REPORTER" --config="$WEB_JSHINTRC" || ret=$?
else
    jshint "$file_to_lint" --reporter="$JSHINT_REPORTER" || ret=$?
fi

exit $ret
