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
from core.controllers.misc.parseOptions import parseXML
from core.controllers.basePlugin.basePlugin import basePlugin
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
        self._options = parseXML(self._configurable.getOptionsXML())
        self._memory = {}
        self._plainOptions = {}
        for o in self._options.keys():
            k = str(o)
            v = str(self._options[o]['default']) 
            self._memory[k] = [v]
            self._plainOptions [k] = v
        self._groupOptionsByTabId()
        self._loadHelp('config')
      

    def _cmd_view(self, params):
        #col1Len = max([len(o) for o in self._options.keys()]) + 4
        #col2Len = 16
        table = [['Setting', 'Value', 'Description']]
        for tabid in self._tabbedOptions.keys():
            tabOpts = self._tabbedOptions[tabid]
            table += [[o, tabOpts[o]['default'], tabOpts[o]['desc']] \
                for o in tabOpts ]           
            table.append([])
        if len(table) > 1:
            table.pop()
        self._console.drawTable(table, True)

    def _groupOptionsByTabId(self):      
        self._tabbedOptions = {}
        for o in self._options.keys():
            opt = self._options[o]
            if opt.has_key('tabid'):
                tabid = str(opt['tabid'])
            else:
                tabid = ''

            if tabid not in self._tabbedOptions:
                target = {}
                self._tabbedOptions[tabid] = target
            else:
                target = self._tabbedOptions[tabid]

            target[o] = opt
                

    def _cmd_set(self, params):
        if len(params) < 2:
            om.out.console('Invalid call to set, please see the help:')
            self._cmd_help(['set'])
        elif not self._options.has_key(params[0]):
            raise w3afException('Unknown option: ' + params[0])
        else:
            name = params[0]
            value = ''.join(params[1:])
            self._options[name]['default'] = value
            self._plainOptions[name] = value
            mem = self._memory[name]
            if value not in mem:
                mem.append(value)
            if isinstance( self._configurable, basePlugin ):
                self._w3af.setPluginOptions( self._configurable.getType(),\
                    self._configurable.getName(), self._options )
                om.out.setPluginOptions( self._configurable.getName() , self._options )
            else:
                try:
                    self._configurable.setOptions( self._options )
                except w3afException, w3:
                    om.out.error( str(w3) )

    

    def _para_set(self, params, part):
        if len(params) == 0:
            
            result = suggest(map(str, self._options.keys()), part)
            return result
        elif len(params) == 1:
            paramName = params[0]
            if paramName not in self._options:
                return []

            opts = self._options[paramName]
            paramType = str(opts['type'])
            if paramType == 'boolean':
                values = [str(opts['default']) == 'True' and 'False' or 'True']
            else:
                values = self._memory[paramName]


            return suggest(values, part)
        else:
            return []

