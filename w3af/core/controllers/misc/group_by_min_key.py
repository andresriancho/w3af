"""
group_by_min_key.py

Copyright 2006 Andres Riancho

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
from itertools import groupby
from operator import itemgetter


def group_by_min_key(input_list):
    """
    This function takes a list with tuples of length two inside:
        [(1,'a'),(1,'b'),('c',True),('d','x')]

    And return a dict with a list as value:
        {1:['a','b'], 'c': [True], 'd':['x']}

    The good thing about this function is that it will find the min key, as you
    saw, in the first case 1, 'c' and 'd' were selected as keys (the items on
    the left of the tuples); but if the input is this:
        [(1,'a'),(2,'a'),('c','a'),('d','x')]

    It will return a dict with a list as value:
        {'a':[1,2,'c'], 'x':['d']}

    Additionally, this function returns the item number of the tuple that was
    used to groupby ( 0 or 1 ).

    This function was created to show information to the user in a better way.

    >>> group_by_min_key( [('a', 1) , ('a', 2) , ('a', 3)] )
    ({'a': [1, 2, 3]}, 0)

    >>> group_by_min_key( [(1, 'a') , (2, 'a') , (3, 'a')] )
    ({'a': [1, 2, 3]}, 1)

    >>> group_by_min_key( [(1, 'a') , (2, 'a') , (3, 'a'), (56, 'd')] )
    ({'a': [1, 2, 3], 'd': [56]}, 1)

    >>> group_by_min_key( [('a', 1) , ('b', 2)] )
    ({'a': [1], 'b': [2]}, 0)

    """
    # So, first, we groupby the first item in the tuples
    key = itemgetter(0)
    value = itemgetter(1)
    res_dict_1 = {}
    for key, group in groupby(input_list, key):
        res_dict_1[key] = [value(x) for x in group]

    # Now, we groupby the second item in the tuples
    key = itemgetter(1)
    value = itemgetter(0)
    res_dict_2 = {}
    for key, group in groupby(input_list, key):
        res_dict_2[key] = [value(x) for x in group]

    # Finally we compare which dict has more keys, and return the one with
    # less keys.
    if len(res_dict_1) > len(res_dict_2):
        return res_dict_2, 1
    else:
        return res_dict_1, 0
