"""
unixctrl.py

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
import termios
import tty
import sys
import os

from w3af.core.ui.console.io.common import (KEY_UP, KEY_DOWN, KEY_RIGHT,
                                            KEY_LEFT, KEY_HOME, KEY_END,
                                            KEY_BACKSPACE)

import w3af.core.controllers.output_manager as om


LONGEST_SEQUENCE = 5

CSI = '\x1B['

CSI_EL = CSI + '%iK'
EL_FW = 0
EL_BACK = 1
EL_WHOLE = 2

CSI_SCP = CSI + 's'
CSI_RCP = CSI + 'u'

CSI_CUU = CSI + '%iA'
CSI_CUD = CSI + '%iB'
CSI_CUF = CSI + '%iC'
CSI_CUB = CSI + '%iD'

SEQ_PREFIX = '\x1B'


def read(amt):
    return sys.stdin.read(amt)

old_settings = None


def set_raw_input_mode(raw):
    """
    Sets the raw input mode for the linux terminal.
    
    :param raw: Boolean to indicate if we want to turn raw mode on or off.
    """
    if not os.isatty(sys.stdin.fileno()):
        return
    
    global old_settings
    
    if raw and old_settings is None:
        fd = sys.stdin.fileno()
        try:
            old_settings = termios.tcgetattr(fd)
            tty.setraw(sys.stdin.fileno())
        except Exception, e:
            om.out.console('termios error: ' + str(e))
    
    elif not (raw or old_settings is None):
        try:
            termios.tcsetattr(sys.stdin.fileno(),
                              termios.TCSADRAIN,
                              old_settings)
            old_settings = None
        except Exception, e:
            om.out.console('termios error: ' + str(e))


def normalizeSequence(sequence):
    if sequence in (KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT):
        return sequence
    map = {'\x1B[7~': KEY_HOME, '\x1B[8~': KEY_END}
    if sequence in map:
        return map[sequence]
    return None


def _moveDelta(delta, pos_code, neg_code):
    if delta != 0:
        code = delta > 0 and pos_code or neg_code
        sys.stdout.write(code % abs(delta))


def moveDelta(dx=1, dy=0):
    _moveDelta(dx, CSI_CUF, CSI_CUB)
    _moveDelta(dy, CSI_CUD, CSI_CUU)


def moveBack(steps=1):
    if steps > 0:
        sys.stdout.write(CSI_CUB % steps)


def moveForward(steps=1):
    if steps > 0:
        sys.stdout.write(CSI_CUF % steps)


def clearScreen():
    """Clears the screen"""
    sys.stdout.write(SEQ_PREFIX + '[H' + SEQ_PREFIX + '[2J')
