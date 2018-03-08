# -*- coding: UTF-8 -*-
"""
cookie_parser.py

Copyright 2015 Andres Riancho

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
import Cookie
import sys

# Cookie pickling bug is fixed in Python 2.7.9 and Python 3.4.3+
# http://bugs.python.org/issue22775
COOKIE_PICKLES_PROPERLY = (
    (sys.version_info[:2] == (2, 7) and sys.version_info >= (2, 7, 9)) or
    sys.version_info >= (3, 4, 3)
)

COOKIE_HEADERS = ('set-cookie', 'cookie', 'cookie2')


class SerializableSimpleCookie(Cookie.SimpleCookie):
    """
    Had to sub-class in order to be able to correctly serialize cookies

    https://code.djangoproject.com/ticket/15863
    https://code.djangoproject.com/attachment/ticket/15863/ticket_15863.diff
    """
    if not COOKIE_PICKLES_PROPERLY:
        def __setitem__(self, key, value):
            # Apply the fix from http://bugs.python.org/issue22775 where
            # it's not fixed in Python itself
            if isinstance(value, Cookie.Morsel):
                # allow assignment of constructed Morsels (e.g. for pickling)
                dict.__setitem__(self, key, value)
            else:
                super(SerializableSimpleCookie, self).__setitem__(key, value)


def parse_cookie(cookie_header_value):
    """
    Parses the value of a "Set-Cookie" header into a Cookie.SimpleCookie object

    :param cookie_header_value: The value of the "Set-Cookie" header
    :return: A Cookie.SimpleCookie instance. Might raise exceptions if the
             cookie value is not in valid format
    """
    cookie_object = SerializableSimpleCookie()

    # FIXME: Workaround for bug in Python's Cookie.py
    #
    # if type(rawdata) == type(""):
    #     self.__ParseString(rawdata)
    #
    # Should read "if isinstance(rawdata, basestring)"
    cookie_header_value = cookie_header_value.encode('utf-8')

    # Note to self: This line may print some chars to the console
    cookie_object.load(cookie_header_value)

    return cookie_object
