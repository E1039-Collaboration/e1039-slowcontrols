#!/bin/bash

INFILE=chages.txt

# Read the input file line by line
while read -r LINE
do
    printf '%s\n' "$LINE"
done < "$INFILE"
