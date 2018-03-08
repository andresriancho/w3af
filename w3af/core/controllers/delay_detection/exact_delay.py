"""
exact_delay.py

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


class ExactDelay(object):
    """
    A simple representation of a delay string like "sleep(%s)"
    """
    def __init__(self, delay_fmt, delta=0, mult=1):
        """
        :param delay_fmt: The format that should be use to generate the delay
                          string. Example: "sleep(%s)".
        """
        self._delay_fmt = delay_fmt
        self._delay_delta = delta
        self._delay_multiplier = mult

    def get_string_for_delay(self, seconds):
        """
        Applies :param seconds to self._delay_fmt

        >>> d = ExactDelay('sleep(%s)')
        >>> d.get_string_for_delay(3)
        'sleep(3)'
        """
        res = ((seconds * self._delay_multiplier) + self._delay_delta)
        return self._delay_fmt % res

    def set_delay_delta(self, delta):
        """
        Some commands are strange... if you want to delay for 5 seconds you
        need to set the value to 6; or 4... This value is added to the seconds:

        >>> d = ExactDelay('sleep(%s)')

        >>> d.get_string_for_delay(3)
        'sleep(3)'

        >>> d.set_delay_delta(1)
        >>> d.get_string_for_delay(3)
        'sleep(4)'

        """
        self._delay_delta = delta

    def set_multiplier(self, mult):
        """
        Some delays are expressed in milliseconds, so we need to take that into
        account and let the user define a specific delay with 1000 as multiplier

        >>> d = ExactDelay('sleep(%s)', mult=1000)

        >>> d.get_string_for_delay(3)
        'sleep(3000)'

        """
        self._delay_multiplier = mult

    def __repr__(self):
        return u'<ExactDelay (fmt:%s, delta:%s, mult:%s)>' % (self._delay_fmt,
                                                              self._delay_delta,
                                                              self._delay_multiplier)
