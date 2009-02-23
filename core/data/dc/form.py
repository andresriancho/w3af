'''
form.py

Copyright 2006 Andres Riancho

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

from core.data.dc.dataContainer import dataContainer
import copy
import urllib


class form(dataContainer):
    '''
    This class represents a HTML form.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, init_val=(), strict=False):
        dataContainer.__init__(self)
        self._method = None
        self._action = None
        self._types = {}
        self._files = []
        self._submitMap = {}
        
    def getAction(self):
        '''
        @return: The form action.
        '''
        return self._action
        
    def setAction(self, action):
        self._action = action
        
    def getMethod(self):
        '''
        @return: The form method.
        '''
        return self._method
    
    def setMethod(self, method):
        self._method = method.upper()
    
    def getFileVariables( self ):
        return self._files
        
    def addFileInput( self, attrs ):
        '''
        Adds a file input to the form
        @parameter attrs: attrs=[("class", "screen")]
        '''
        name = ''
        
        for attr in attrs:
            if attr[0] == 'name':
                name = attr[1]
                break
        
        if not name:
            for attr in attrs:
                if attr[0] == 'id':
                    name = attr[1]
                    break
        
        if name:
            self._files.append( name )
            self[name] = ''
    
    def __str__( self ):
        '''
        This method returns a string representation of the form Object.
        @return: string representation of the form Object.
        '''
        tmp = self.copy()
        for i in self._submitMap:
            tmp[i] = self._submitMap[i]
        return urllib.urlencode( tmp )
    
    def copy(self):
        '''
        This method returns a copy of the form Object.
        
        @return: A copy of myself.
        '''
        return copy.deepcopy( self )
        
    def addSubmit( self, name, value ):
        '''
        This is something I havent thought about !
        <input type="submit" name="b0f" value="Submit Request">
        '''
        self._submitMap[name] = value
        
    def addInput(self, attrs):
        '''
        Adds a input to the form
        
        @parameter attrs: attrs=[("class", "screen")]
        '''

        '''
        <INPUT type="text" name="email"><BR>
        <INPUT type="radio" name="sex" value="Male"> Male<BR>
        '''
        
        type = name = value = ''
            
        for attr in attrs:
            if attr[0] == 'name' or attr[0] == 'id':
                name = attr[1]

        if name != '':
            # Find the type
            for attr in attrs:
                if attr[0] == 'type':
                    type = attr[1]

            # Find the default value
            for attr in attrs:
                if attr[0] == 'value':
                    value = attr[1]

            if type == 'submit':
                self.addSubmit( name, value )
            else:
                self._types[name] = type 
                self[name] = value
        
    def getType( self, name ):
        return self._types[name]
