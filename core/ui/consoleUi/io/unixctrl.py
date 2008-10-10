'''
unixctrl.py

Copyright 2008 Andres Riancho

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

import sys
from core.ui.consoleUi.io.common import *
import core.controllers.outputManager as om
import termios, tty

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

def read( amt ):
    return sys.stdin.read( amt )

oldSettings = None
def setRawInputMode( raw ):
    '''
    Sets the raw input mode, in linux.
    '''
    global oldSettings
    if raw and oldSettings is None:
        fd = sys.stdin.fileno()
        try:
            oldSettings = termios.tcgetattr(fd)
            tty.setraw(sys.stdin.fileno())
        except Exception, e:
            om.out.console('termios error: ' + str(e) )
    elif not (raw or oldSettings is None):
        try:
            termios.tcsetattr( sys.stdin.fileno() , termios.TCSADRAIN, oldSettings )
            oldSettings = None
        except Exception, e:
            om.out.console('termios error: ' + str(e) )


def normalizeSequence(sequence):
    if sequence in (KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT):
        return sequence
    map = { '\x1B[7~': KEY_HOME, '\x1B[8~': KEY_END } 
    if sequence in map:
        return map[sequence]
    return None

def _moveDelta(delta, pos_code, neg_code):
	if delta != 0:
		code = delta > 0 and pos_code or neg_code
		sys.stdout.write (code % abs(delta))

def moveDelta(dx=1, dy=0):
	_moveDelta(dx, CSI_CUF, CSI_CUB)
	_moveDelta(dy, CSI_CUD, CSI_CUU)

def moveBack(steps=1):
    if steps>0:
    	sys.stdout.write(CSI_CUB % steps)

def moveForward(steps=1):
    if steps>0:
    	sys.stdout.write(CSI_CUF % steps)

def clearScreen():
    """Clears the screen"""
    sys.stdout.write(SEQ_PREFIX + '[H' + SEQ_PREFIX + '[2J')
