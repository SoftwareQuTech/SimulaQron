#!/usr/bin/env python3

import sys


def main(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


if __name__ == '__main__':
    module_name = sys.argv[1]
    exists = main(module_name)
    if exists:
        print('Y')
    else:
        print("N")
