#!/bin/bash

file_to_lint="$1"
mode="$2"

if [ "$mode" == "node" -o "$mode" == "nodejs" ]
  then
    echo "Linting assuming node.js"
    jscs "$file_to_lint"
    jshint "$file_to_lint" --config="/usr/share/node.jshintrc"
elif [ "$mode" == "web" -o "$mode" == "webjs" ]
  then
    echo "Linting assuming web (normal) js"
    jscs "$file_to_lint"
    jshint "$file_to_lint" --config="/usr/share/web.jshintrc"
else
    echo "Linting based on closest configuration file"
    jscs "$file_to_lint"
    jshint "$file_to_lint"
fi

exit 0
