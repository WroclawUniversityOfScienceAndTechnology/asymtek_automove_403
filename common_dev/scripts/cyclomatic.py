#!/usr/bin/env python3


import lizard

# to exclude directory use -x <dir_path> param
params = [lizard, "/repo/src/", "-C", "25", "-w"]

if __name__ == "__main__":
    lizard.main(params)
