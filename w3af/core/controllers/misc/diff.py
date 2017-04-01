"""
diff.py

Copyright 2008 Andres Riancho

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
import difflib


def diff(a, b):
    """
    :param a: A string
    :param b: A string (similar to a)
    :return: Two strings (a_mod, b_mod) which are basically:

                a_mod = a - (a intersection b)
                b_mod = b - (a intersection b)

             Or if you want to see it in another way, the results are the
             parts of the string that make it unique between each other.

    >>> diff('123456', '123a56')
    ('4', 'a')

    >>> diff('yes 123abc', 'no 123abc')
    ('yes', 'no')

    >>> diff('123abc yes', '123abc no')
    ('yes', 'no')

    >>> diff('123abc yes', 'no 123abc no')
    ('yes', 'no no')
    """
    matching_blocks = difflib.SequenceMatcher(None, a, b).get_matching_blocks()
    removed_a = 0
    removed_b = 0

    for block in matching_blocks:
        a_index, b_index, size = block
        a = a[:a_index - removed_a] + a[a_index - removed_a + size:]
        b = b[:b_index - removed_b] + b[b_index - removed_b + size:]
        removed_a += size
        removed_b += size

    return a, b
