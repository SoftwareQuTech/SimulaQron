#!/usr/bin/env python3

import os


def main():
    path_to_this_file = os.path.abspath(__file__)
    path_to_this_folder = os.path.dirname(path_to_this_file)
    simulaqron_path = os.path.split(path_to_this_folder)[0]
    return simulaqron_path


if __name__ == '__main__':
    simulaqron_path = main()
    print(simulaqron_path)
