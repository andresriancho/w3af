"""
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

"""
import w3af.core.controllers.output_manager as om

from w3af.core.ui.console.menu import menu
from w3af.core.ui.console.util import suggest
from w3af.core.data.options.option_list import OptionList
from w3af.core.controllers.plugins.plugin import Plugin
from w3af.core.controllers.exceptions import BaseFrameworkException


class ConfigMenu(menu):
    """
    Generic menu for configuring the configurable items.
    It is used to configure plugins and set url and misc settings.

    :author: Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    """

    def __init__(self, name, console, w3af, parent, configurable):
        menu.__init__(self, 'config:' + name, console, w3af, parent)

        self._configurable = configurable
        self._options = self._configurable.get_options()
        self._unsaved_options = {}
        self._opt_dict = {}
        self._memory = {}

        for o in self._options:
            k = o.get_name()
            v = o.get_default_value()
            self._memory[k] = [v]
            self._opt_dict[k] = o

        self._group_options_by_tabid()
        self._load_help('config')

    def _cmd_view(self, params):
        """
        View the configurable options for the self._configurable instance in a
        table.
        """
        # Some configurable objects require us to reload the options each time
        # we're going to show them in the console.
        # https://github.com/andresriancho/w3af/issues/291
        self._options = self._configurable.get_options()
        self._group_options_by_tabid()
        
        table = [['Setting', 'Value', 'Modified', 'Description']]
        for tabid in self._tabbed_options.keys():
            tab_opts = self._tabbed_options[tabid]

            for opt_name in tab_opts:
                opt = self._options[opt_name]

                if opt_name in self._unsaved_options:
                    unsaved_name = opt_name
                    row = [unsaved_name, self._unsaved_options[opt_name], 'Yes', opt.get_desc()]
                else:
                    row = [opt_name, opt.get_value_str(), '', opt.get_desc()]
                table.append(row)

            table.append([])
        if len(table) > 1:
            table.pop()
        self._console.draw_table(table, True)

    def _group_options_by_tabid(self):
        self._tabbed_options = {}
        for opt in self._options:
            tabid = opt.get_tabid()

            if tabid not in self._tabbed_options:
                target = {}
                self._tabbed_options[tabid] = target
            else:
                target = self._tabbed_options[tabid]

            target[opt.get_name()] = opt

    def _cmd_set(self, params):
        if len(params) < 2:
            om.out.console('Invalid call to set, please see the help:')
            self._cmd_help(['set'])
            return
            
        if params[0] not in self._options:
            raise BaseFrameworkException('Unknown option: "%s".' % params[0])
        
        name = params[0]
        value = ' '.join(params[1:])
        
        # This set_value might raise a BaseFrameworkException, for example this
        # might happen when the configuration parameter is an integer and
        # the user sets it to 'abc'
        try:
            self._options[name].set_value(value)
            self._unsaved_options[name] = value
        except BaseFrameworkException, e:
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
        try:
            for unsaved_opt_name, unsaved_val in self._unsaved_options.iteritems():
                self._options[unsaved_opt_name].set_value(unsaved_val)

            # Save the options using the corresponding setter
            self._configurable.set_options(self._options)

            if isinstance(self._configurable, Plugin):
                self._w3af.plugins.set_plugin_options(
                    self._configurable.get_type(),
                    self._configurable.get_name(),
                    self._options)

        except BaseFrameworkException, e:
            msg = 'Identified an error with the user-defined settings:\n\n'\
                  '    - %s \n\n'\
                  'No information has been saved.'
            raise BaseFrameworkException(msg % e)
        else:
            om.out.console('The configuration has been saved.')
            self._unsaved_options = {}
    
    def _cmd_back(self, tokens):
        try:
            self._cmd_save(tokens)
        except BaseFrameworkException, e:
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
                values = [opt.get_default_value() == 'True' and 'False' or 'True']
            else:
                values = self._memory[paramName]

            return suggest(values, part)
        else:
            return []

    def _cmd_help(self, params):
        if len(params) == 1:
            optName = params[0]
            if optName in self._opt_dict:
                opt = self._opt_dict[optName]
                om.out.console(opt.get_desc())
                if opt.get_help():
                    om.out.console('')
                    om.out.console(opt.get_help())
                om.out.console("Type: %s" % opt.get_type())
                om.out.console(
                    'Current value is: "%s"' % opt.get_default_value())
                return

        menu._cmd_help(self, params)

    def _para_help(self, params, part):
        result = menu._para_help(self, params, part)
        result.extend(suggest(self._opt_dict, part))
        return result
