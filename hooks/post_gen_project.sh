#!/usr/bin/env sh

echo "-------------------------------------------------------------------------------"
echo
echo "Skeleton generated."

echo "Please fix the following TODOs before you use the generated files:"
grep --color=always --recursive --context=3 --line-number TODO .

echo
echo "-------------------------------------------------------------------------------"
echo

echo "You might also want add this new module to your instance requirements inside the setup.py"

rm -r misc/
