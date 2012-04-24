'''
config.py

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

from core.ui.consoleUi.menu import *
from core.ui.consoleUi.util import *
from core.controllers.basePlugin.basePlugin import basePlugin
from core.controllers.basePlugin.baseOutputPlugin import baseOutputPlugin
from core.controllers.w3afException import w3afException
        
class configMenu(menu):
    '''
    Generic menu for configuring the configurable items.
    It is used to configure plugins and set url and misc settings.
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''

    def __init__(self, name, console, w3af, parent, configurable):
        menu.__init__(self, 'config:' + name, console, w3af, parent)
        self._configurable = configurable
        self._options = self._configurable.getOptions()
        self._optDict = {}
        self._memory = {}
        self._plainOptions = {}
        for o in self._options:
            k = o.getName()
            v = o.getDefaultValue()
            self._memory[k] = [v]
            self._plainOptions[k] = v
            self._optDict[k] = o
        self._groupOptionsByTabId()
        self._loadHelp('config')
      

    def _cmd_view(self, params):
        #col1Len = max([len(o) for o in self._options.keys()]) + 4
        #col2Len = 16
        table = [['Setting', 'Value', 'Description']]
        for tabid in self._tabbedOptions.keys():
            tabOpts = self._tabbedOptions[tabid]
            table += [[o, tabOpts[o].getValueStr(), tabOpts[o].getDesc()] \
                for o in tabOpts ]           
            table.append([])
        if len(table) > 1:
            table.pop()
        self._console.drawTable(table, True)

    def _groupOptionsByTabId(self):      
        self._tabbedOptions = {}
        for opt in self._options:
            tabid = opt.getTabId()

            if tabid not in self._tabbedOptions:
                target = {}
                self._tabbedOptions[tabid] = target
            else:
                target = self._tabbedOptions[tabid]
            
            target[opt.getName()] = opt

    def _cmd_set(self, params):
        if len(params) < 2:
            om.out.console('Invalid call to set, please see the help:')
            self._cmd_help(['set'])
        elif params[0] not in self._options:
            raise w3afException('Unknown option: ' + params[0])
        else:
            name = params[0]
            value = ''.join(params[1:])

            self._options[name].setValue( value )
            self._plainOptions[name] = value
                            
            if isinstance( self._configurable, basePlugin ):
                self._w3af.plugins.setPluginOptions( self._configurable.getType(),
                                                     self._configurable.getName(),
                                                     self._options )
                if value not in self._memory[name]:
                    self._memory[name].append(value)                
            else:
                try:
                    self._configurable.setOptions( self._options )
                    if value not in self._memory[name]:
                        self._memory[name].append(value)                    
                except w3afException, w3:
                    om.out.error( str(w3) )


    def _para_set(self, params, part):
        if len(params) == 0:
            result = suggest( [ i.getName() for i in self._options] , part)
            return result
        elif len(params) == 1:
            paramName = params[0]
            if paramName not in self._options:
                return []

            opt = self._options[paramName]
            paramType = opt.getType()
            if paramType == 'boolean':
                values = [ opt.getDefaultValue() == 'True' and 'False' or 'True']
            else:
                values = self._memory[paramName]


            return suggest(values, part)
        else:
            return []


    def _cmd_help(self, params):
        if len(params)==1:
            optName = params[0]
            if optName in self._optDict:
                opt = self._optDict[optName]
                om.out.console(opt.getDesc())
                om.out.console("Type: %s" % opt.getType())
                om.out.console("Current value is: %s" % opt.getDefaultValue())
                return

        menu._cmd_help(self, params)

    def _para_help(self, params, part):
        result = menu._para_help(self, params, part)
        result.extend(suggest(self._optDict, part))
        return result
