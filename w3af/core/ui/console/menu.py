"""
menu.py

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
import pprint

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.ui.console.util import splitPath, suggest
from w3af.core.ui.console.history import history
from w3af.core.ui.console.help import helpMainRepository, HelpContainer


class menu(object):
    """
    Menu objects handle the commands and completion requests.
    Menus form an hierarchy and are able to delegate requests to their children.
    
    :author: Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    """
    def __init__(self, name, console, w3af, parent=None, **other):
        self._name = name
        self._history = history()

        self._help = HelpContainer()
        self._keysHelp = HelpContainer()
        self._w3af = w3af
        self._handlers = {}
        self._parent = parent
        self._console = console
        self._children = {}
        self._child_call = False
        
        self._load_help('common')
        helpMainRepository.load_help('keys', self._keysHelp)

        self._initHandlers()

    def suggest(self, tokens, part, onlyLocalCommands=False):
        """
        Suggest the possible completions
        :param tokens: list of string
        :param part: base for completion
        """
        if len(tokens) == 0:
            return self.suggest_commands(part, onlyLocalCommands)
        return self.suggest_params(tokens[0], tokens[1:], part)

    def is_raw(self=None):
        return False

    def get_path(self):
        if self._parent is None:
            return self._name
        else:
            return self._parent.get_path() + '/' + self._name

    def get_history(self):
        return self._history

    def _initHandlers(self):
        self._universalCommands = ['back', 'exit', 'keys', 'print']

        self._paramHandlers = {}
        for cmd in [c for c in dir(self) if c.startswith('_cmd_')]:
            self._handlers[cmd[5:]] = getattr(self, cmd)

        for cmd in self._handlers.keys():
            try:
                pHandler = getattr(self, '_para_' + cmd)
                self._paramHandlers[cmd] = pHandler
            except:
                pass

    def _load_help(self, name, vars=None):
        helpMainRepository.load_help(name, self._help, vars)
#        self._help = load_help(name, self._help, vars)

    def addChild(self, name, constructor):
        if type(constructor) in (tuple, list):
            constructor, params = constructor[0], constructor[1:]
        else:
            params = []

        self._children[name] = constructor(
            name, self._console, self._w3af, self, *params)

    def suggest_commands(self, part='', onlyLocal=False):

        first, rest = splitPath(part)

        if rest is None:
            # the command must be in the current menu
            result = suggest(self.get_commands(onlyLocal), part)
            if self.get_children() is not None:
                result += suggest(self.get_children(), part)
            return result
        else:
            try:
                # delegate to the children
                subMenu = self.get_children()[first]
                return subMenu.suggest_commands(rest, True)
            except:
                return []

    def suggest_params(self, command, params, part):
        if command in self._paramHandlers:
            return self._paramHandlers[command](params, part)

        children = self.get_children()
        if command in children:
            child = children[command]
            return child.suggest(params, part, True)

    def get_commands(self, onlyLocal=False):
        """
        By default, commands are defined by methods _cmd_<command>.
        """
        cmds = self._handlers.keys()

        if onlyLocal:
            cmds = [c for c in cmds if c not in self._universalCommands]

        return cmds

    def get_children(self):
        return self._children

    def get_handler(self, command):
        try:
            return self._handlers[command]
        except:
            return None

    def set_child_call(self, true_false):
        """
        This will set _child_call to True for handling the "set" command:
            w3af>>> target set target http://w3af.org/
        
        While this won't ever set it to true:
            w3af>>> target
            w3af/config:target>>> set target http://w3af.org/
        """
        self._child_call = true_false

    def execute(self, tokens):

        if len(tokens) == 0:
            return self

        command, params = tokens[0], tokens[1:]
        handler = self.get_handler(command)
        if handler:
            return handler(params)

        children = self.get_children()
        if command in children:
            child = children[command]
            child.set_child_call(True)
            try:
                return child.execute(params)
            finally:
                child.set_child_call(False)

        raise BaseFrameworkException("Unknown command '%s'" % command)

    def _cmd_back(self, tokens):
        return self._console.back

    def _cmd_exit(self, tokens):
        return self._console.exit

    def _cmd_help(self, params, brief=False):
        if len(params) == 0:
            table = self._help.get_plain_help_table(True)
            self._console.draw_table(table)
        else:
            subj = params[0]
            short, full = self._help.get_help(subj)
            if short is None:
                raise BaseFrameworkException("No help for '%s'" % subj)

            om.out.console(short)
            if full:
                om.out.console(full)

    def _cmd_keys(self, params=None):
        table = self._keysHelp.get_plain_help_table(True)
        self._console.draw_table(table)

    def _cmd_print(self, params):
        if not len(params):
            raise BaseFrameworkException('Variable is expected')

        small_locals = {'kb': kb, 'w3af_core': self._w3af}
        small_globals = {}

        eval_variable = ' '.join(params)
        try:
            res = eval(eval_variable, small_globals, small_locals)
        except:
            om.out.console('Unknown variable.')
        else:
            pp = pprint.PrettyPrinter(indent=4)
            output = pp.pformat(res)
            om.out.console(output)

    def _para_help(self, params, part):
        if len(params) == 0:
            return suggest(self._help.get_items(), part)
        else:
            return []

    def join(self):
        """
        This is a abstract method to emulate the join
        method on a thread, by default DO NOTHING
        """
        pass
