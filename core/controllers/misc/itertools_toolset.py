'''
itertools_toolset.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
import itertools
import operator

#
#    Source for this code was taken from http://docs.python.org/library/itertools.html
#
def unique_everseen(iterable, key=None):
    """
    List unique elements, preserving order. Remember all elements ever seen.
    
    >>> [x for x in unique_everseen('AAAABBBCCDAABBB')]
    ['A', 'B', 'C', 'D']
    >>> [x for x in unique_everseen('ABBCcAD', str.lower)]
    ['A', 'B', 'C', 'D']
    
    """
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in itertools.ifilterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element

def unique_justseen(iterable, key=None):
    """
    List unique elements, preserving order. Remember only the element just seen.

    >>> [x for x in unique_justseen('AAAABBBCCDAABBB')]
    ['A', 'B', 'C', 'D', 'A', 'B']
    >>> [x for x in unique_justseen('ABBCcAD', str.lower)]
    ['A', 'B', 'C', 'A', 'D']
    """
    imap = itertools.imap
    itemgetter = operator.itemgetter
    groupby = itertools.groupby
    return imap(next, imap(itemgetter(1), groupby(iterable, key)))
