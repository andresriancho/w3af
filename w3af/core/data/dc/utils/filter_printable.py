# -*- coding: utf-8 -*-
"""
filter_printable.py

Copyright 2014 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import string

from itertools import imap, groupby
from operator import itemgetter


NON_PRINTABLE_REPLACE = '.'


def is_printable_chr(c):
    return c in string.printable


def unique_justseen(iterable, key=None):
    "List unique elements, preserving order. Remember only the element just seen."
    # unique_justseen('AAAABBBCCDAABBB') --> A B C D A B
    # unique_justseen('ABBCcAD', str.lower) --> A B C A D
    return imap(next, imap(itemgetter(1), groupby(iterable, key)))


def filter_non_printable(_str):
    chars = []

    for c in str(_str):
        if is_printable_chr(c):
            chars.append(c)
        else:
            chars.append(NON_PRINTABLE_REPLACE)

    return ''.join(unique_justseen(chars))