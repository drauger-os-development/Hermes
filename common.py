#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  common.py
#
#  Copyright 2025 Thomas Castleman <batcastle@draugeros.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
"""Common Functions for Hermes"""
G = "\033[92m"
R = "\033[91m"
NC = "\033[0m"
Y = "\033[93m"
B = '\033[94m'


def eprint(args, *kwargs, color=R):
    """Print to stderr easier"""
    print(color, file=sys.stderr, end="")
    print(args, file=sys.stderr, *kwargs, end="")
    print(NC, file=sys.stderr)


def unique(starting_list):
    """Function to get a list down to only unique elements"""
    # initialize a null list
    # unique_list = []
    # traverse for all elements
    # for each in starting_list:
        # check if exists in unique_list or not
        # if each not in unique_list:
            # unique_list.append(each)
    # return unique_list
    return list(set(starting_list))
