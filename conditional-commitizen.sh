#!/bin/sh
log=$(git log origin/HEAD..HEAD | wc -l)
if [ "$log" -gt 0 ]; then cz check --rev-range origin/HEAD..HEAD; fi
