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
import core.data.kb.info as info
import core.data.kb.vuln as vuln
from core.ui.consoleUi.util import *
from core.ui.consoleUi.history import *
from core.ui.consoleUi.help import *
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
from core.ui.consoleUi.menu import *

class kbMenu(menu):

    '''
    This menu is used to display information from the knowledge base
    and (in the nearest future) to manipulate it.
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''
    def __init__(self, name, console, w3af, parent=None, **other):
        menu.__init__(self, name, console, core, parent)
        self._loadHelp( 'kb' )

        # A mapping of KB data types to how to display it.
        # Key of the data type => (KB getter, (column names), (column getters))k
        self.__getters = {
            'vulns': (
                kb.kb.getAllVulns, 
                ['Vulnerabilities'], 
                [vuln.vuln.getDesc]),
            'info':  (
                kb.kb.getAllInfos,
                ['Info'],
                [info.info.getDesc])
        }

    def _list_objects(self, descriptor, objs):
        colNames = descriptor[0]
        colGetters = descriptor[1]
        result = []
        result.append(colNames)
        result.append([])

        for obj in objs:
            row = []
            for getter in colGetters:
                row.append(getter(obj))

            result.append(row)

        self._console.drawTable(result)


    def _cmd_list(self, params):
        if len(params)>0:
            for p in params:
                if p in self.__getters:
                    desc = self.__getters[p]
                    self._list_objects(desc[1:], desc[0]())
                else:
                    om.out.console('Type %s is unknown' % p)
        else:
            om.out.console('Parameter type is missed, see the help:')
            self._cmd_help(['list'])
            

    def _para_list(self, params, part):
        if len(params):
            return []

        return suggest(self.__getters.keys(), part) 
