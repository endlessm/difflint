#!/bin/bash

file_to_lint="$1"
mode="$2"
ret=0

if [ "$mode" == "node" -o "$mode" == "nodejs" ]
  then
    echo "Linting assuming node.js"
    jscs "$file_to_lint" || ret=$?
    NODE_JSHINTRC=`python3 -c 'print(__import__("pkg_resources").resource_filename("difflint", "data/node.jshintrc"))'`
    jshint "$file_to_lint" --config="$NODE_JSHINTRC" || ret=$?
elif [ "$mode" == "web" -o "$mode" == "webjs" ]
  then
    echo "Linting assuming web (normal) js"
    jscs "$file_to_lint" || ret=$?
    WEB_JSHINTRC=`python3 -c 'print(__import__("pkg_resources").resource_filename("difflint", "data/web.jshintrc"))'`
    jshint "$file_to_lint" --config="$WEB_JSHINTRC" || ret=$?
else
    echo "Linting based on closest configuration file"
    jscs "$file_to_lint" || ret=$?
    jshint "$file_to_lint" || ret=$?
fi

exit $ret
