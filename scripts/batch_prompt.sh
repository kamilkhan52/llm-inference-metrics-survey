#!/bin/bash
# print the paper list for batch $1
awk -F'\t' -v b="$1" 'NR>1 && $7==b {printf "- %s | arXiv %s | %s | %s | %s\n",$1,($2==""?"none":$2),$4,$3,$5}' ./SELECTION.tsv
