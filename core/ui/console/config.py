'''
config.py

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

'''
import core.controllers.output_manager as om

from core.ui.console.menu import menu
from core.ui.console.util import suggest
from core.controllers.plugins.plugin import Plugin
from core.controllers.exceptions import w3afException


class ConfigMenu(menu):
    '''
    Generic menu for configuring the configurable items.
    It is used to configure plugins and set url and misc settings.
    :author: Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''

    def __init__(self, name, console, w3af, parent, configurable):
        menu.__init__(self, 'config:' + name, console, w3af, parent)
        self._configurable = configurable
        self._options = self._configurable.get_options()
        self._optDict = {}
        self._memory = {}
        self._plain_options = {}
        for o in self._options:
            k = o.get_name()
            v = o.get_default_value()
            self._memory[k] = [v]
            self._plain_options[k] = v
            self._optDict[k] = o
        self._groupOptionsByTabId()
        self._load_help('config')

    def _cmd_view(self, params):
        # Some configurable objects require us to reload the options each time
        # we're going to show them in the console.
        # https://github.com/andresriancho/w3af/issues/291
        self._options = self._configurable.get_options()
        self._groupOptionsByTabId()
        
        table = [['Setting', 'Value', 'Description']]
        for tabid in self._tabbedOptions.keys():
            tabOpts = self._tabbedOptions[tabid]
            table += [[o, tabOpts[o].get_value_str(), tabOpts[o].get_desc()]
                      for o in tabOpts]
            table.append([])
        if len(table) > 1:
            table.pop()
        self._console.draw_table(table, True)

    def _groupOptionsByTabId(self):
        self._tabbedOptions = {}
        for opt in self._options:
            tabid = opt.get_tabid()

            if tabid not in self._tabbedOptions:
                target = {}
                self._tabbedOptions[tabid] = target
            else:
                target = self._tabbedOptions[tabid]

            target[opt.get_name()] = opt

    def _cmd_set(self, params):
        if len(params) < 2:
            om.out.console('Invalid call to set, please see the help:')
            self._cmd_help(['set'])
            
        elif params[0] not in self._options:
            raise w3afException('Unknown option: "%s".' % params[0])
        
        else:
            name = params[0]
            value = ' '.join(params[1:])
            
            # This set_value might raise a w3afException, for example this
            # might happen when the configuration parameter is an integer and
            # the user sets it to 'abc'
            try:
                self._options[name].set_value(value)
                self._plain_options[name] = value
            except w3afException, e:
                om.out.error(str(e))
            else:
                if value not in self._memory[name]:
                    self._memory[name].append(value)

            # All the options are set to the configurable on "back", this is
            # to handle the issue of configuration parameters which depend on
            # each other: https://github.com/andresriancho/w3af/issues/108
            # @see: _cmd_back()
            #
            # There is an exception to that rule, calling:
            #    w3af>>> target set target http://w3af.org/
            #
            # Is different from calling:
            #    w3af>>> target
            #    w3af/config:target>>> set target http://w3af.org/
            #
            # The first one has an implied save:
            if self._child_call:
                self._cmd_save([])
    
    def _cmd_save(self, tokens):
        # Save the options using the corresponding setter
        if isinstance(self._configurable, Plugin):
            self._w3af.plugins.set_plugin_options(
                self._configurable.get_type(),
                self._configurable.get_name(),
                self._options)
        else:
            self._configurable.set_options(self._options)
        try:
            # Save the options using the corresponding setter
            if isinstance(self._configurable, Plugin):
                self._w3af.plugins.set_plugin_options(
                    self._configurable.get_type(),
                    self._configurable.get_name(),
                    self._options)
            else:
                self._configurable.set_options(self._options)
                
        except w3afException, e:
            msg = 'Identified an error with the user-defined settings:\n\n'\
                  '    - %s\n\n'\
                  'No information has been saved.'
            raise w3afException(msg % e)
        else:
            om.out.console('The configuration has been saved.')
    
    def _cmd_back(self, tokens):
        try:
            self._cmd_save(tokens)
        except w3afException, e:
            om.out.error(str(e))

        return self._console.back

    def _para_set(self, params, part):
        if len(params) == 0:
            result = suggest([i.get_name() for i in self._options], part)
            return result
        elif len(params) == 1:
            paramName = params[0]
            if paramName not in self._options:
                return []

            opt = self._options[paramName]
            paramType = opt.get_type()
            if paramType == 'boolean':
                values = [opt.get_default_value(
                ) == 'True' and 'False' or 'True']
            else:
                values = self._memory[paramName]

            return suggest(values, part)
        else:
            return []

    def _cmd_help(self, params):
        if len(params) == 1:
            optName = params[0]
            if optName in self._optDict:
                opt = self._optDict[optName]
                om.out.console(opt.get_desc())
                om.out.console("Type: %s" % opt.get_type())
                om.out.console(
                    "Current value is: %s" % opt.get_default_value())
                return

        menu._cmd_help(self, params)

    def _para_help(self, params, part):
        result = menu._para_help(self, params, part)
        result.extend(suggest(self._optDict, part))
        return result
