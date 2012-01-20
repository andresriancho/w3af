'''
config.py

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

class config(dict):
    '''
    This class saves config parameters sent by the user.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
        
    def save(self, variableName, value):
        '''
        This method saves the variableName value to a dict.
        '''
        self[variableName] = value
        
    def getData(self, variableName, default=None):
        '''
        @return: Returns the data that was saved to the variableName
        '''
        return self.get(variableName, default)
        
cf = config()
