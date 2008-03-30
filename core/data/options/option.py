'''
option.py

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

class option:
    '''
    This class represents an option.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, name, defaultValue, desc, type, help='', tabid=''):
        '''
        @parameter name: The name of the option
        @parameter defaultValue: The default value of the option
        @parameter desc: The description of the option
        @parameter type: boolean, integer, string, etc..
        @parameter help: The help of the option; a large description of the option
        @parameter tabid: The tab id of the option
        '''
        self._name = name
        self._value = self._defaultValue = defaultValue
        self._desc = desc
        self._type = type
        self._help = help
        self._tabid = tabid
    
    def getName( self ): return self._name
    def getDesc( self ): return self._desc
    def getDefaultValue( self ): return self._defaultValue
    # This is the value configured by the user; this is the only variable that 
    # ain't put in the __str__
    def getValue( self ): return self._value
    
    def getType( self ): return self._type
    def getHelp( self ): return self._help
    def getTabId( self ): return self._tabid
    
    def setName( self, v ): self._name = v
    def setDesc( self, v ): self._desc = v
    def setDefaultValue( self, v ): self._defaultValue = v
    def setValue( self, v ): self._value = v
    def setType( self, v ): self._type = v
    def setHelp( self, v ): self._help = v
    def setTabId( self, v ): self._tabid = v
    
    def __str__( self ):
        '''
        The idea if to generate something like this:
        
        <Option name="onlyForward">\
            <default>'+str(self._onlyForward)+'</default>\
            <desc>When spidering, only search directories inside the one that was given as a parameter</desc>\
            <help>Something something...</help>\
            <type>boolean</type>\
            <tabid>Tab1</tabid>\
        </Option>\
        '''
        res = '<Option name="'+self._sanitize(str(self._name))+'">\n'
        res += '    <default>'+self._sanitize(str(self._defaultValue))+'</default>\n'
        res += '    <desc>'+self._sanitize(str(self._desc))+'</desc>\n'
        res += '    <type>'+self._sanitize(str(self._type))+'</type>\n'
        if self._help:
            res += '    <help>'+self._sanitize(str(self._help))+'</help>\n'
        if self._tabid:
            res += '    <tabid>'+self._sanitize(str(self._tabid))+'</tabid>\n'
        res +='</Option>'
        return res
        
    def _sanitize( self, value ):
        '''
        Encode some values that can't be used in XML
        '''
        return value
        
    def copy(self):
        '''
        This method returns a copy of the option Object.
        
        @return: A copy of myself.
        '''
        return copy.copy( self )
        
