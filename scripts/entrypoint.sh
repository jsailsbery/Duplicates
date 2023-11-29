#!/bin/bash

case "$1" in
  find_duplicates)
    shift
    python scripts/find_duplicates.py "$@"
    ;;
  # Add more cases for other scripts here
  *)
    echo "Unknown script: $1"
    exit 1
    ;;
esac
