"""
greek.py

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

_abbrevs = [
    (1 << 50L, 'P'),
    (1 << 40L, 'T'),
    (1 << 30L, 'G'),
    (1 << 20L, 'M'),
    (1 << 10L, 'k'),
    (1, '')
]


def greek(size):
    """
    Return a string representing the greek/metric suffix of a size
    """
    for factor, suffix in _abbrevs:
        if size > factor:
            break
    return str(int(size / factor)) + suffix
