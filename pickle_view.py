#!/usr/bin/env python

# Simple script to view the contents of a cookie file (JSON, or the legacy pickle format).
# Viewing never modifies the file.

import json
import pickle
import sys

if __name__ == '__main__':
    argv = sys.argv
    if len(argv) <= 1:
        print("Specify a cookies file as a parameter, e.g. cookies/user.pkl")
    else:
        with open(argv[1], 'rb') as f:
            raw = f.read()
        print(pickle.loads(raw) if raw.startswith(b"\x80") else json.loads(raw))
