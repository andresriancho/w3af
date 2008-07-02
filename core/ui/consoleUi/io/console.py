'''
posixterm.py

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

#import core.controllers.outputManager as om
import sys
import os

# If this two modules are imported here instead of below
# we loose windows support.
#import tty
#import termios

#from ecma48 import *

from core.controllers.w3afException import w3afException


CTRL_CODES = range(1,27)
CTRL_CODES.remove(9)
CTRL_CODES.remove(13)

def write(s):
    if (len(s)):
        sys.stdout.write(s)

def writeln(s=''):
    sys.stdout.write(s+'\n\r')

def bell():
    sys.stdout.write('\x07')

def backspace():
    sys.stdout.write(KEY_BACKSPACE)

def getch(buf=None):
    ch = read(1)
    if ch == SEQ_PREFIX:
        buf = [ ch ]
        result = getch(buf)
    elif buf is not None:
        buf.append(ch)
        strval = ''.join(buf)
        posixVal = normalizeSequence(strval)
        if posixVal:
            return posixVal
	elif len(buf)>LONGEST_SEQUENCE:
            return getch()
	else:
            return getch(buf)
    elif ord(ch) in CTRL_CODES:
        result = '^' + chr(ord(ch)+64)
    else:
        result = ch

    return result

def wrapper( fun ):
    try:
        setRawInputMode(True)
        fun()
    finally:
        setRawInputMode(False)

def ioctl_GWINSZ(fd): #### TABULATION FUNCTIONS
    try: ### Discover terminal width
        import fcntl, termios, struct
        cr = struct.unpack('hh',
        fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
    except:
        return None
    return cr

def terminal_size():
    ### decide on *some* terminal size
    # try open fds
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
    # ...then ctty
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    
    if not cr:
        # env vars or finally defaults
        try:
            cr = (os.environ['LINES'], os.environ['COLUMNS'])
        except:
            cr = (25, 80)
    # reverse rows, cols
    return int(cr[1]), int(cr[0])


try:
    import tty, termios
    from core.ui.consoleUi.io.unixctrl import * 
except Exception, e:
    # We arent on unix !
    try:
        import msvcrt
        from core.ui.consoleUi.io.winctrl import * 
    except Exception, a:
        print str(e + '\n' + a)
        # We arent on windows nor unix
        raise w3afException('w3af support for OS X aint available yet! Please contribute.')

#extKeys = [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT]

