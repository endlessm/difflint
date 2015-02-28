#!/bin/bash

file_to_lint="$1"
mode="$2"
ret=0

if [ "$mode" == "node" -o "$mode" == "nodejs" ]
  then
    echo "Linting assuming node.js"
    jscs "$file_to_lint" || ret=$?
    jshint "$file_to_lint" --config="/usr/share/node.jshintrc" || ret=$?
elif [ "$mode" == "web" -o "$mode" == "webjs" ]
  then
    echo "Linting assuming web (normal) js"
    jscs "$file_to_lint" || ret=$?
    jshint "$file_to_lint" --config="/usr/share/web.jshintrc" || ret=$?
else
    echo "Linting based on closest configuration file"
    jscs "$file_to_lint" || ret=$?
    jshint "$file_to_lint" || ret=$?
fi

exit $ret
