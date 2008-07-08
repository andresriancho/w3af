'''
comboOption.py

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

import copy
import cgi
import re
from core.controllers.w3afException import w3afException
from core.data.options.option import option

class comboOption(option):
    '''
    This class represents an comboOption.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, name, defaultValue, desc, type, help='', tabid=''):
        '''
        @parameter name: The name of the comboOption
        @parameter defaultValue: The default value of the comboOption; it is a list of the options that the user can choose from.
        @parameter desc: The description of the comboOption
        @parameter type: boolean, integer, string, etc..
        @parameter help: The help of the comboOption; a large description of the comboOption
        @parameter tabid: The tab id of the comboOption
        '''
        self._name = name
        self._value = defaultValue[0]
        self._defaultValue = defaultValue[0]
        self._comboOptions = defaultValue
        self._desc = desc
        self._type = type
        self._help = help
        self._tabid = tabid

    def getComboOptions(self):
        return self._comboOptions

    def setValue( self, value ):
        '''
        @parameter value: The value parameter is set by the user interface, which for example sends 'a' when the
        options of the combobox are '1','2','a','f'
        '''
        print "setting in combo:", value
        if value in self._comboOptions:
            self._value = value
        else:
            raise w3afException('The option you selected is invalid.')
