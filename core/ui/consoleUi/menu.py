'''
menu.py

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

import traceback
        
import core.data.kb.knowledgeBase as kb        
from core.ui.consoleUi.util import *
from core.ui.consoleUi.history import *
from core.ui.consoleUi.help import *
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException

class menu:
    '''
    Menu objects handle the commands and completion requests.
    Menus form an hierarchy and are able to delegate requests to their children.
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''

    def suggest(self, tokens, part):
        '''
        Suggest the possible completions
        @parameter tokens: list of string
        @parameter part: base for completion
        '''
        if len(tokens)==0:
            return self.suggestCommands(part)
        return self.suggestParams(tokens[0], tokens[1:], part)

    def isRaw(self=None):
        return False

    def getPath(self):
        if self._parent is None:
            return self._name
        else:
            return self._parent.getPath() + '/' + self._name

    def getHistory(self):
        return self._history

    def __init__(self, name, console, w3af, parent=None, **other):
        self._name = name
        self._history = history()
        
        self._help = help()
        self._keysHelp = help()
        self._w3af = w3af
        self._handlers = {}
        self._parent = parent
        self._console = console
        self._children = {}

        self._loadHelp('common')
        helpMainRepository.loadHelp('keys', self._keysHelp)
#        self._keysHelp = {} 

        self._initHandlers()

#            if cmd not in helpTab:
                # highlight undocumented items
#                self._help.addHelpEntry(cmd, 'UNDOCUMENTED', 'menu')

    def _initHandlers( self ):
        self._paramHandlers = {}
        for cmd in [c for c in dir(self) if c.startswith('_cmd_')]:
            self._handlers[cmd[5:]] =  getattr(self, cmd)

        for cmd in self.getCommands():
            try:
                pHandler = getattr(self, '_para_'+cmd)
                self._paramHandlers[cmd] = pHandler
            except:
                pass

    def _loadHelp(self, name, vars=None):
        helpMainRepository.loadHelp(name, self._help, vars)
#        self._help = loadHelp(name, self._help, vars)


    def addChild(self, name, constructor):
        if type(constructor) in (tuple, list):
            constructor, params = constructor[0], constructor[1:]
        else:
            params = []

        self._children[name] = constructor(name, self._console, self._w3af, self, *params)

        

    def suggestCommands(self, part=''):

        first, rest = splitPath(part)

        if rest is None:
            # the command must be in the current menu
            result = suggest(self.getCommands(), part)
            if self.getChildren() is not None:
                result +=   suggest(self.getChildren(), part)
            return result
        else:
            try:
                # delegate to the children
                subMenu = self.getChildren()[first]
                return subMenu.suggestCommands(rest)
            except:
                return []

    def suggestParams(self, command, params, part):
        if command in self._paramHandlers:
            return self._paramHandlers[command](params, part)

        children = self.getChildren()
        if command in children:
            child = children[command]
            return child.suggest(params, part)


    def getCommands(self):
        '''
        By default, commands are defined by methods _cmd_<command>.
        '''
        return self._handlers.keys()

    def getChildren(self):
        return self._children #self.getCommands()

    def getHandler(self, command):
        try:
            return self._handlers[command]
        except:
            return None
            

    def execute(self, tokens):

        if len(tokens) == 0:
            return self

        command, params = tokens[0], tokens[1:]
        handler = self.getHandler( command )
        if handler:
            return handler( params )

        children = self.getChildren()
        if command in children:
            child = children[command]
            return child.execute( params )

        raise w3afException("Unknown command '%s'" % command)


    def _cmd_back(self, tokens):
        return self._console.back

    def _cmd_exit(self, tokens):
        return self._console.exit


    def _cmd_help(self, params, brief=False):
        if len(params) == 0:
            table = self._help.getPlainHelpTable(True)
            self._console.drawTable(table)
        else:
            subj = params[0]
            short, full = self._help.getHelp(subj)
            if short is None:
                raise w3afException("No help for '%s'" % subj)

            om.out.console(short)
            if full:
                om.out.console(full)
                

    def _cmd_keys(self, params=None):
        table = self._keysHelp.getPlainHelpTable(True)
        self._console.drawTable(table)
        

    def _cmd_assert(self, params):
        if not len(params):
            raise w3afException('Expression is expected')

        assertCommand = 'assert '
        assertCommand += ' '.join( params )
        try:
            exec( assertCommand )
        except AssertionError, ae:
            msg = 'Assert **FAILED**'

            try:
                # Get the value of the first argument
                a = params[0]
                # FIXME: The exec should have a restricted globals and locals
                exec( 'aRes = ' + a )
            except:
                pass
            else:
                msg += ' : ' + a + ' == ' + str(aRes)
            om.out.error( msg )
        except Exception, e:
            om.out.error('An unexpected exception was raised during assertion: ' + str(e) )
            om.out.error('The executed command was: ' + assertCommand )
        else:
            om.out.console('Assert succeded.')
        
        return None

    def _getHelpForSubj(self, subj):
        table = self.getBriefHelp()
        if table.has_key(subj):
            return help[subj]
        else:
            return None

           
    def _para_help(self, params, part):
        if len(params) ==0:
            return suggest(self._help.getItems(), part)
        else:
            return []

           
