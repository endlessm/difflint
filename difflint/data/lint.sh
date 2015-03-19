#!/bin/bash

file_to_lint="$1"
mode="$2"
ret=0

JSCS_REPORTER=`python3 -c 'print(__import__("pkg_resources").resource_filename("difflint", "data/jscs_terse_reporter.js"))'`

if [ "$mode" == "node" -o "$mode" == "nodejs" ]
  then
    NODE_JSHINTRC=`python3 -c 'print(__import__("pkg_resources").resource_filename("difflint", "data/node.jshintrc"))'`
    jscs "$file_to_lint" --reporter="$JSCS_REPORTER" || ret=$?
    jshint "$file_to_lint" --config="$NODE_JSHINTRC" || ret=$?
elif [ "$mode" == "web" -o "$mode" == "webjs" ]
  then
    WEB_JSHINTRC=`python3 -c 'print(__import__("pkg_resources").resource_filename("difflint", "data/web.jshintrc"))'`
    jscs "$file_to_lint" --reporter="$JSCS_REPORTER" || ret=$?
    jshint "$file_to_lint" --config="$WEB_JSHINTRC" || ret=$?
else
    jscs "$file_to_lint" --reporter="$JSCS_REPORTER" || ret=$?
    jshint "$file_to_lint" || ret=$?
fi

exit $ret
