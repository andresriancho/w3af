"""
winctrl.py

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
import sys

try:
    import msvcrt
except ImportError:
    # This only works on windows, and was PASSing before because of a bug (+x
    # in the winctrl.py file). Now that I've removed the +x nosetests does load/
    # import this file and builds fail.
    #
    # Create a mock just to allow nosetests/pylint to PASS
    #
    # https://circleci.com/gh/andresriancho/w3af/1495
    class msvcrt(object):
        @staticmethod
        def getch():
            pass

from w3af.core.ui.console.io.common import *


SEQ_PREFIX = '\xE0'
LONGEST_SEQUENCE = 2

win2UnixMap = {
    '\xE0\x48': KEY_UP,
    '\xE0\x50': KEY_DOWN,
    '\xE0\x4D': KEY_RIGHT,
    '\xE0\x4B': KEY_LEFT,
    '\xE0\x47': KEY_HOME,
    '\xE0\x4F': KEY_END
}


def read(amt):
    res = ''
    for i in xrange(amt):
        res += msvcrt.getch()
    return res


def set_raw_input_mode(raw):
    """
    Sets the raw input mode, in windows.
    """
    pass


def normalizeSequence(seq):
    if seq in win2UnixMap:
        return win2UnixMap[seq]
    return None


def moveBack(steps=1):
    for i in range(steps):
        sys.stdout.write('\x08')


def clearScreen():
    """Clears the screen (Plug)"""
    pass
