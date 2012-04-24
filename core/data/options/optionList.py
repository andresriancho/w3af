'''
optionList.py

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

from core.controllers.w3afException import w3afException

class optionList(object):
    '''
    This class represents a list of options.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        self._oList = []
        
    def add( self, option ):
        self._oList.append( option )
    append = add
    
    def __len__( self ):
        return len(self._oList)
    
    def __repr__(self):
        '''
        A nice way of printing your object =)
        '''
        return '<optionList: '+ '|'.join([i.getName() for i in self._oList]) +'>'

    def __eq__(self, other):
        if not isinstance(other, optionList):
            return False
        
        return self._oList == other._oList
            
        
    def __contains__( self, item_name ):
        for o in self._oList:
            if o.getName() == item_name:
                return True
        return False
    
    def __getitem__( self, item_name ):
        '''
        This method is used when on any configurable object the developer does something like:
        
        def setOptions( self, optionsList ):
            self._checkPersistent = optionsList['checkPersistent']
            
        @return: The value of the item that was selected
        '''
        try:
            item_name = int(item_name)
        except:
            # A string
            for o in self._oList:
                if o.getName() == item_name:
                    return o
            raise w3afException('The optionList object doesn\'t contain an option with the name: ' + item_name )
        else:
            # An integer
            return self._oList[ item_name ]
