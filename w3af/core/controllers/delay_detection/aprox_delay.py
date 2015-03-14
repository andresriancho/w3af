"""
aprox_delay.py

Copyright 2012 Andres Riancho

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


class AproxDelay(object):
    """
    A simple representation of a delay string like "sleep(%s)"
    """
    def __init__(self, delay_fmt, delay_char, char_reps):
        """
        :param delay_fmt: The format that should be use to generate the delay
                          string. Example: 'a@a.%sX!'.
        
        :param delay_char: The character that will be repeated to complete the
                           delay_fmt
        
        :param char_reps: The number of times the char will be repeated.
        """
        self._delay_fmt = delay_fmt
        self._delay_char = delay_char
        self._char_reps = char_reps
        self._base_multiplier = 1
        
    def get_string_for_multiplier(self, multiplier):
        """
        Applies :param multiplier to self._delay_fmt

        >>> d = AproxDelay('a@a.%sX!', 'a', 10)
        >>> d.get_string_for_multiplier( 2 )
        'a@a.aaaaaaaaaaaaaaaaaaaaX!'
        """
        fmt_data = self._delay_char * self._char_reps * multiplier * self._base_multiplier
        return self._delay_fmt % fmt_data
    
    def set_base_multiplier(self, multiplier):
        self._base_multiplier = multiplier

    def __repr__(self):
        return u'<AproxDelay (fmt:%s, char:%s, reps:%s)>' % (self._delay_fmt,
                                                             self._delay_char,
                                                             self._char_reps)

