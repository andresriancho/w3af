'''
consoleUi.py

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
try:
    from shlex import *
    import os
    import random
    import traceback
    from core.controllers.auto_update import UIUpdater
    from core.controllers.misc.homeDir import verify_dir_has_perm
    from core.ui.consoleUi.rootMenu import *
    from core.ui.consoleUi.callbackMenu import *
    from core.ui.consoleUi.util import *
    import core.ui.consoleUi.io.console as term
    from core.ui.consoleUi.history import *
    import core.ui.consoleUi.tables as tables
    import core.controllers.w3afCore
    import core.controllers.outputManager as om
    import core.controllers.miscSettings as miscSettings
    from core.controllers.w3afException import w3afException, \
        w3afMustStopException
except KeyboardInterrupt:
    sys.exit(0)


class ConsoleUIUpdater(UIUpdater):
    
    def __init__(self, force, rev):
        
        # Output function
        log = om.out.console
        # Ask user function
        def ask(msg):
            return raw_input(msg + ' [y/N] ').lower() in ('y', 'yes')

        UIUpdater.__init__(self, force=force, ask=ask,
                           logger=log, rev=rev, print_result=True)
        
        # Show revisions logs function
        def show_log(msg, get_logs):
            if ask(msg):
                log(get_logs())
        # Add callbacks
        self._add_callback('callback_onupdate_confirm', ask)
        self._add_callback('callback_onupdate_show_log', show_log)
    
    def _handle_update_output(self, upd_output):
        # Nothing special to do here.
        pass

class consoleUi:
    '''
    This class represents the console. 
    It handles the keys pressed and delegate the completion and execution tasks 
    to the current menu.
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''

    def __init__(self, commands=[], parent=None, do_upd=None, rev=0):
        self._commands = commands 
        self._line = [] # the line which is being typed
        self._position = 0 # cursor position
        self._history = historyTable() # each menu has array of (array, positionInArray)
        self._trace = []
        self._upd_avail = False

        self._handlers = {
            '\t' : self._onTab,
            '\r' : self._onEnter,
            term.KEY_BACKSPACE : self._onBackspace,
            term.KEY_LEFT : self._onLeft,
            term.KEY_RIGHT : self._onRight,
            term.KEY_UP : self._onUp,
            term.KEY_DOWN : self._onDown,
            '^C' : self._backOrExit,
            '^D' : self._backOrExit,
            '^L' : self._clearScreen,
            '^W' : self._delWord,
            '^H' : self._onBackspace,
            '^A' : self._toLineStart,
            '^E' : self._toLineEnd
        }

        if parent:
            self.__initFromParent(parent)
        else:
            self.__initRoot(do_upd, rev)

    def __initRoot(self, do_upd, rev):
        '''
        Root menu init routine.
        '''     
        cons_upd = ConsoleUIUpdater(force=do_upd, rev=rev)
        cons_upd.update()
        # Core initialization
        self._w3af = core.controllers.w3afCore.w3afCore()
        self._w3af.plugins.setPlugins(['console'], 'output')

    def __initFromParent(self, parent):
        self._context = parent._context
        self._w3af = parent._w3af
        
    def sh(self, name='w3af', callback=None):
        '''
        Main cycle
        '''
        try:
            if callback:
                if hasattr(self, '_context'):
                    ctx = self._context
                else:
                    ctx = None
                self._context = callbackMenu(name, self, self._w3af, ctx, callback)
            else:
                self._context = rootMenu(name, self, self._w3af)
                
            self._lastWasArrow = False
            self._showPrompt()
            self._active = True
            term.setRawInputMode(True)

            self._executePending()

            while self._active: 
                try:
                    c = term.getch()
                    self._handleKey(c)
                except Exception, e:
                    om.out.console(str(e))

            term.setRawInputMode(False)
        except KeyboardInterrupt:
            pass

        if not hasattr(self, '_parent'):
            self._w3af.quit()
            self._context.join()
            om.out.console(self._randomMessage())


    def _executePending(self):
        while (self._commands):
            curCmd, self._commands = self._commands[0], self._commands[1:]
            self._paste(curCmd)
            self._onEnter()

    def write(self, s):
        om.out.console(s)
    
    def writeln(self, s=''):
        om.out.console(s+'\n')

    def term_width(self):
        return term.terminal_size()[0]

           
    def drawTable(self, lines, header=False):
        table = tables.table(lines)
        table.draw(self.term_width(), header)
        
        
    def back(self):
        if len(self._trace) == 0:
            return None
        else:
            return self._trace.pop()

    def _initPrompt(self):
        self._position = 0
        self._line = []
#        self._showPrompt()

    def inRawLineMode( self ):
        return hasattr(self._context, 'isRaw') and self._context.isRaw()

    def exit(self):
        self._active = False

    def _getHistory(self):
        return self._context.getHistory()

    def _setHistory(self, hist):
        path = self._context.getPath()
        self._history[path] = (hist, [])
    
    def _handleKey(self, key):
        try:
            if self._handlers.has_key(key):
                self._handlers[key]()
            else:
                self._paste(key)
        except Exception, e:
            traceback.print_exc() # TODO

    def _backOrExit(self):
        exit = len(self._trace)==0
        if self.inRawLineMode():
            # temporary hack for exploit interaction mode
            # possibly, menu should have it's 'exit' method
            self._context = self.back()
            om.out.console('')
        else:
            cmd = exit and 'exit' or 'back'
            self._clearLine()
            self._paste(cmd)
            self._execute()
        if not exit:
            self._initPrompt()
            self._showPrompt()

    def _clearLine(self):
        self._toLineEnd()
        while self._position:
            self._onBackspace()

    def _onBackspace(self):
        if self._position >0:
            self._position -= 1
            del self._line[self._position]
            term.moveBack(1)            
#            lenToErase = len(self._line[:self._position])+1
#            term.write (' ' * lenToErase)
#            term.moveBack (lenToErase)

#            term.eraseLine()
            self._line.append(' ')
            self._showTail()
            del self._line[-1]
#            term.write(' ')

    def _clearScreen(self):
        """Clears the screen"""
        term.clearScreen()
        self._initPrompt()
        self._showPrompt()

    def _execute(self):
        # term.writeln()

        line = self._getLineStr()
        term.setRawInputMode(False)
        om.out.console('')
        if len(line) and not line.isspace():

            self._getHistory().remember(self._line)
    
            try:               
                # New menu is the result of any command.
                # If None, the menu is not changed.
                params = self.inRawLineMode() and line or self._parseLine(line)
                menu = self._context.execute(params)
            except w3afMustStopException:
                menu = None
                self.exit()

            except w3afException, e:
                menu = None
                om.out.console( e.value )
                
            if menu:
                if callable(menu):
                    
                    # Command is able to delegate the detection 
                    # of the new menu to the console 
                    # (that's useful for back command:
                    # otherwise it's not clear what must be added to the trace)
                    # It's kind of hack, but I had no time 
                    # to think of anything better.
                    # An other option is to allow menu 
                    # objects modify console state directly which I don't like
                    # -- Sasha
                    menu = menu() 
                    
                elif menu != self._context:
                    # Remember this for the back command
                    self._trace.append(self._context)
                if menu is not None:
                    self._context = menu
        term.setRawInputMode(True)


    def _onEnter(self):
        self._execute()
        self._initPrompt()
        self._showPrompt()

    def _delWord(self):
        filt = str.isspace
        while (True):
            if self._position == 0:
                break

            char = self._line[self._position-1]

            if filt(char):
                self._onBackspace()
            elif filt==str.isspace:
                filt = str.isalnum(char) and str.isalnum \
                    or (lambda s: not s.isalnum())
            else:
                break

    def _toLineEnd(self):
        self._moveDelta(len(self._line) - self._position)
        self._position = len(self._line)

    def _toLineStart(self):
        term.moveBack(self._position)
        self._position = 0

    def _onTab(self):
        '''
            Autocompletion logic is called here
        '''

        # TODO: autocomplete for raw menu
        if self.inRawLineMode():
            return

        line = self._getLineStr()[:self._position] # take the line before the cursor
        tokens = self._parseLine(line)
        if not line.endswith(' ') and len(tokens)>0:
            # if the cursor is after non-space, the last word is used 
            # as a hint for autocompletion
            incomplete = tokens.pop()
        else:
            incomplete = ''

        completions = self._context.suggest(tokens, incomplete)
        if completions is None:
            return
        prefix = commonPrefix(completions)
        if prefix != '':
            self._paste(prefix)
        elif len(completions) > 0:
            term.writeln()
            for variant in map(lambda c: c[1], completions):
                term.write(variant + ' ')
            term.writeln()
            
            self._showPrompt()

            self._showLine()
        else:
            term.bell()
    
    def _onLeft(self):
        if self._position > 0:
            self._position -= 1
            term.moveBack()
        else:
            term.bell()
    
    def _onRight(self):
        if self._position < len(self._line):
#            self._position += 1
            self._moveForward()
        else:
            term.bell()

    def _onUp(self):
        history = self._getHistory()
        newLine = history.back(self._line)

        if newLine is not None:
            self._setLine(newLine)
        else:
            term.bell()

    def _onDown(self):
        history = self._getHistory()
        newLine = history.forward()
        if newLine is not None:
            self._setLine(newLine)
        else:
            term.bell()

    def _setLine(self, line):
        term.moveBack(self._position)
        term.write(' ' * len(self._line))
        term.moveBack(len(self._line))
#        term.eraseLine()
        term.write(''.join(line))
        self._line = line
        self._position = len(line)

    def _getLineStr(self):
        return ''.join(self._line)

    def _parseLine(self, line=None):
        if line is None:
            line = self._getLineStr()
        result = []
        parser = shlex(line)
        parser.whitespace_split = True
        while True:
            try:
                token = parser.get_token()
            except ValueError, ve:
                term.write( str(ve) + '\n')
                result = []
                break
            else:
                if token == parser.eof:
                    break
                result.append(token)

        return result

    def _paste(self, text):

#        term.savePosition()
        tail = self._line[self._position:]
        for c in text:
            self._line.insert(self._position, c)
            self._position += 1

        term.write(text)
        term.write(''.join(tail))
#        term.restorePosition()  
        term.moveBack(len(tail))
        

    def _showPrompt(self):
        term.write(self._context.getPath() + ">>> ")
        
    def _showLine(self):
        strLine = self._getLineStr()
        term.write(strLine)
        self._moveDelta(self._position - len(strLine))

    def _moveForward(self, steps=1):
        for i in range(steps):
            if self._position == len(self._line): term.bell()
        term.write(self._line[self._position])
        self._position += 1

    def _moveDelta(self, steps):
        if steps:
            if steps>0:
                self._moveForward(steps)
            else:
                term.moveBack(-steps)


    def _showTail(self, retainPosition=True):
        '''
            reprint everything that should be after the cursor
        '''
#        term.savePosition()
        strLine = self._getLineStr()
        toWrite = strLine[self._position:]
        term.write(toWrite)
        if retainPosition:
            term.moveBack(len(toWrite))

#        term.restorePosition()


    def _randomMessage(self):
        f = file('core/ui/consoleUi/exitMessages.txt', 'r')
        lines = f.readlines()
        idx = random.randrange(len(lines))
        line = lines[idx]
        return '\n' + line
        
        

