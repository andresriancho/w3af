'''
consoleMenu.py

Copyright 2006 Andres Riancho

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

# Some traditional imports
import traceback
import sys
from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
import re
            
class consoleMenu:
    '''
    This class is a menu for console.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )    
    '''
    def __init__( self ):
        self._spacesSettings = 20
        self._commandHistory = []
        self._commandIndex = 0
        self._lastKeyWasArrow = False
        
    def _parse( self, command ):
        '''
        Parses the user input.
        
        @return: A command and its parameters in a tuple.
        '''
        self._commandHistory.append( command )
        
        c = command.split(' ')[0]
        paramString = ' '.join( command.split(' ')[1:] )

        p = []
        p.append('')
        longParam = False
        escaping = False

        for char in paramString:
            if char == '\\':
                escaping = True
                continue
                
            if not longParam:
                if char == "'" and not escaping:
                    longParam = True
                    p.append('')
                elif char == " ":
                    p.append('')
                else:
                    p[ len(p)-1 ] += char
            else:
                # I'm *inside* a long parameter
                if char == "'" and not escaping:
                    # The long parameter has ended
                    if " " not in p[ len(p)-1 ]:
                        p[ len(p)-1 ] = "'" + p[ len(p)-1 ] + "'"
                    
                    # Go to the next parameter
                    p.append('')
                    longParam = False
                else:
                    p[ len(p)-1 ] += char
                
            
            # Only one character can be escaped
            escaping = False
        
        # Some final cleanup
        p = [ x for x in p if x != '' ]
        return c, p
    
    def _printCommand( self, commandIndex, toRemove ):
        '''
        Prints a command to the console using raw console mode.
        '''
        for i in xrange(toRemove):
            om.out.console( "\b \b", newLine=False )
        res = self._commandHistory[ commandIndex ]
        om.out.console( res , newLine=False )
        return res
        
    def _read( self ):
        def go():
            res = ''
            left = ''
            right = ''
            while True:
                c = read(1)
                if c == '\033':
                    # is an arrow
                    if not self._lastKeyWasArrow:
                        self._commandIndex = len( self._commandHistory ) 
                        self._commandHistory.append( res )
                    
                    self._lastKeyWasArrow = True
                    
                    c = read(2)
                    if c == '[A':
                        #up arrow
                        if self._commandIndex<= 0:
                            om.out.console( "\a", newLine=False )
                        else:
                            self._commandIndex -= 1
                            res = self._printCommand( self._commandIndex, len( res ) )
                    elif c == '[B':
                        #down arrow
                        if self._commandIndex >= (len(self._commandHistory) -1):
                            om.out.console( "\a", newLine=False )
                        else:
                            self._commandIndex += 1
                            res = self._printCommand( self._commandIndex, len( res ) )
                    elif c == '[D':
                        #left arrow
                        if len(res) != 0:
                            om.out.console( "\b \b", newLine=False )
                            res = res[:-1]
                    elif c == '[C':
                        #right arrow
                        #sys.stdout.write("\b")
                        pass
                else:
                    self._lastKeyWasArrow = False
                    if ord(c) == 9:
                        # tab!
                        possible = []
                        for command in self._menu.keys():
                            if command.find( res ) == 0:
                                possible.append( command )
                        
                        if len(possible) == 0:
                            om.out.console( "\a", newLine=False )
                        elif len(possible) == 1:
                            for i in res:
                                om.out.console( "\b \b", newLine=False )
                            res = possible[0] + ' '
                            om.out.console( res , newLine=False )
                        else:
                            for i in res:
                                om.out.console( "\b \b", newLine=False )                        
                            om.out.console( "\n\r", newLine=False )
                            for i in possible:
                                om.out.console( i + "\n\r", newLine=False )
                            om.out.console( self._prompt, newLine=False )
                            om.out.console( res, newLine=False )
                        
                    elif ord(c) == 3:
                        #ctrl+c
                        raise KeyboardInterrupt
                    elif ord(c) == 4:
                        #ctrl+d
                        raise KeyboardInterrupt
                    elif ord(c) == 13:
                        om.out.console( "\n\r", newLine=False )
                        return res
                    # Thanks to Andy_Bach@wiwb.uscourts.gov for reporting a bug
                    # regarding the backspace handling!
                    elif ord(c) == 127 or ord(c) == 8:      #backspace
                        if len(res) != 0:
                            om.out.console( "\b \b", newLine=False )
                            res = res[:-1]
                    # This is the alias requested in [ 1740695 ] Command Line Interface Ease of Use
                    # by Darren B - darrenbi
                    elif c == '.':
                        if res == '':
                            om.out.console( ".\n\r", newLine=False )
                            return 'back'
                        else:
                            res += c
                            om.out.console( c, newLine=False )
                            
                    elif c == '?':
                        command = ''
                        if res.endswith(' '):
                            command = 'help ' + res.split(' ')[0]
                        elif res == '':
                            command = 'help'
                        else:
                            res += '?'
                            om.out.console( "?", newLine=False )
                        
                        if command != '':
                            om.out.console( "?\n\r", newLine=False )
                            self._exec( command.strip() )
                            om.out.console( self._prompt + res, newLine=False )
                    else:
                        res += c
                        om.out.console( c, newLine=False )
        
        if len( self._commands ) != 0:
            command = self._commands.pop()
            om.out.console( command, newLine=True )
            res = command
        
        else:
            setRawInputMode( True )
            try:
                res = go()
            except Exception,e:
                setRawInputMode( False )
                raise e
            else:
                setRawInputMode( False )
        
        return res

    def _mainloop( self, prompt, callback=None ):
        go = True
        self._prompt = prompt
        while go != False:
            om.out.console( prompt, newLine=False )
            try:
                command = self._read()
                if command != '':
                    if callback == None:
                        go = self._exec( command.strip() )
                    else:
                        args = (command,)
                        go = apply( callback, args, {} )
            except w3afException, e:
                setRawInputMode( False )
                om.out.error( str(e) )
            except KeyboardInterrupt,k:
                setRawInputMode( False )
                go = False
                self._back( [] )
                om.out.console( '' )
            except:
                setRawInputMode( False )
                raise
    
    def mprint( self, col1, col2 ):
        '''
        Prints two columns to the console.
        '''
        spaces = self._spacesSettings
        spaces -= len( col1 )
        om.out.console( col1, newLine=False )
        for i in xrange(spaces):
            om.out.console(' ', newLine=False)
        if spaces < 0:
            om.out.console('    ', newLine=False)
        om.out.console( col2 )
        
    def mprintn( self, printList ):
        '''
        Prints N columns to the console, where N is len(printList)
        '''
        for col in printList:
            spaces = self._spacesSettings
            spaces -= len( col )
            om.out.console( col, newLine=False )
            for i in range(spaces):
                om.out.console(' ', newLine=False)
            if spaces < 0:
                om.out.console('    ', newLine=False)
        om.out.console( '' )

def setRawInputMode_win( raw ):
    '''
    Sets the raw input mode, in windows.
    '''
    pass
    
def read_win( amt ):
    res = ''
    for i in xrange( amt ):
        res += msvcrt.getch()
    return res
    
oldSettings = None
def setRawInputMode_unix( raw ):
    '''
    Sets the raw input mode, in linux.
    '''
    global oldSettings
    if raw:
        fd = sys.stdin.fileno()
        try:
            oldSettings = termios.tcgetattr(fd)
            tty.setraw(sys.stdin.fileno())
        except Exception, e:
            om.out.console('termios error: ' + str(e) )
    else:
        if oldSettings == None:
            fd = sys.stdin.fileno()
            try:
                oldSettings = termios.tcgetattr(fd)
            except Exception, e:
                om.out.console('termios error: ' + str(e) )
        try:
            termios.tcsetattr( sys.stdin.fileno() , termios.TCSADRAIN, oldSettings )
        except Exception, e:
            om.out.console('termios error: ' + str(e) )

def read_unix( amt ):
    return sys.stdin.read( amt )

try:
    import tty, termios
except:
    # We arent on unix !
    try:
        import msvcrt
    except:
        # We arent on windows nor unix
        raise w3afException('w3af support for OS X aint available yet! Please contribute.')
    else:
        setRawInputMode = setRawInputMode_win
        read = read_win
else:
    setRawInputMode = setRawInputMode_unix
    read = read_unix
