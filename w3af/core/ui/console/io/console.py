"""
console.py

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
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.exceptions import BaseFrameworkException


CTRL_CODES = range(1, 27)
CTRL_CODES.remove(9)
CTRL_CODES.remove(13)


def sync_with_om(func):
    """
    Given that the output manager has been migrated into a producer/consumer
    model, the messages that are sent to it are added to a Queue and printed
    "at a random time". The issue with this is that NOT EVERYTHING YOU SEE IN
    THE CONSOLE is printed using the om (see functions below), which ends up
    with unordered messages printed to the console.
    """
    def om_wrapper(*args, **kwds):
        om.manager.process_all_messages()
        return func(*args, **kwds)
    return om_wrapper


@sync_with_om
def write(s):
    if len(s):
        sys.stdout.write(s)


@sync_with_om
def writeln(s=''):
    sys.stdout.write(s + '\n\r')


@sync_with_om
def bell():
    sys.stdout.write('\x07')


@sync_with_om
def backspace():
    sys.stdout.write(KEY_BACKSPACE)


@sync_with_om
def getch(buf=None):
    try:
        ch = read(1)
    except KeyboardInterrupt:
        return getch(buf)
    if ch == SEQ_PREFIX:
        buf = [ch]
        result = getch(buf)
    elif buf is not None:
        buf.append(ch)
        strval = ''.join(buf)
        posixVal = normalizeSequence(strval)
        if posixVal:
            return posixVal
        elif len(buf) > LONGEST_SEQUENCE:
            return getch()
        else:
            return getch(buf)
    elif len(ch) and ord(ch) in CTRL_CODES:
        result = '^' + chr(ord(ch) + 64)
    else:
        result = ch

    return result


def ioctl_GWINSZ(fd):  # TABULATION FUNCTIONS
    try:  # Discover terminal width
        import fcntl
        import termios
        import struct
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


def terminal_width():
    return terminal_size()[0]


try:
    import tty
    import termios
    from w3af.core.ui.console.io.unixctrl import *
except Exception, e:
    # We aren't on unix !
    try:
        import msvcrt
        from w3af.core.ui.console.io.winctrl import *
    except Exception, a:
        print str(e + '\n' + a)
        # We arent on windows nor unix
        raise BaseFrameworkException(
            'w3af support for OS X isn\'t available yet! Please contribute.')

#extKeys = [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT]
