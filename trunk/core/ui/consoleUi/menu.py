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

    def suggest(self, tokens, part, onlyLocalCommands=False):
        '''
        Suggest the possible completions
        @parameter tokens: list of string
        @parameter part: base for completion
        '''
        if len(tokens)==0:
            return self.suggestCommands(part, onlyLocalCommands)
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
        self._universalCommands = ['back', 'exit', 'keys', 'print']
        
        self._paramHandlers = {}
        for cmd in [c for c in dir(self) if c.startswith('_cmd_')]:
            self._handlers[cmd[5:]] =  getattr(self, cmd)

        for cmd in self._handlers.keys():
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

        

    def suggestCommands(self, part='', onlyLocal=False):

        first, rest = splitPath(part)

        if rest is None:
            # the command must be in the current menu
            result = suggest(self.getCommands(onlyLocal), part)
            if self.getChildren() is not None:
                result +=   suggest(self.getChildren(), part)
            return result
        else:
            try:
                # delegate to the children
                subMenu = self.getChildren()[first]
                return subMenu.suggestCommands(rest, True)
            except:
                return []

    def suggestParams(self, command, params, part):
        if command in self._paramHandlers:
            return self._paramHandlers[command](params, part)

        children = self.getChildren()
        if command in children:
            child = children[command]
            return child.suggest(params, part, True)


    def getCommands(self, onlyLocal=False):
        '''
        By default, commands are defined by methods _cmd_<command>.
        '''
        cmds = self._handlers.keys()

        if onlyLocal:
            cmds = [c for c in cmds if c not in self._universalCommands]

        return cmds

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
        

    def _cmd_print(self, params):
        if not len(params):
            raise w3afException('Variable is expected')

        small_locals = {'kb':kb, 'w3af_core':self._w3af }
        small_globals = {}
        
        evalVariable = ' '.join( params )
        try:
            res = eval( evalVariable,  small_globals,  small_locals)
        except:
            om.out.console('Unknown variable.')
        else:
            om.out.console( repr(res) )


    def _cmd_assert(self, params):
        if not len(params):
            raise w3afException('Expression is expected')

        small_locals = {'kb':kb, 'w3af_core':self._w3af }
        small_globals = {}
        
        assert_command = 'assert '
        assert_command += ' '.join( params )
        try:
            exec( assert_command,  small_globals,  small_locals)
        except AssertionError, ae:
            msg = 'Assert **FAILED**'

            aRes = ''
            try:
                # Get the value of the first argument
                a = params[0]
                exec( 'aRes = ' + a,  small_globals,  small_locals)
            except:
                pass
            else:
                msg += ' : ' + a + ' == ' + str(aRes)
            om.out.error( msg )
        except Exception, e:
            om.out.error('An unexpected exception was raised during assertion: ' + str(e) )
            om.out.error('The executed command was: ' + assert_command )
        else:
            om.out.console('Assert succeded.')
        
        return None

    def _para_help(self, params, part):
        if len(params) ==0:
            return suggest(self._help.getItems(), part)
        else:
            return []

    def join(self):
        '''
        This is a abstract method to emulate the join
        method on a thread, by default DO NOTHING
        '''
        pass
