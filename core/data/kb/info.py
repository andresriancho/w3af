'''
info.py

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

from core.data.parsers.urlParser import uri2url
import core.data.constants.severity as severity


class info(dict):
    '''
    This class represents an information that is saved to the kb.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, dataObj=None):
        
        # Default values
        self._url = ''
        self._uri = ''
        self._desc = ''
        self._method = ''
        self._variable = ''
        self._id = None
        self._name = ''
        self._dc = None
        self._string_match = ''
            
        # Clone the info object!
        if isinstance( dataObj, info ):
            self.setURI( dataObj.getURI() )
            self.setDesc( dataObj.getDesc() )
            self.setMethod( dataObj.getMethod() )
            self.setVar( dataObj.getVar() )
            self.setId( dataObj.getId() )
            self.setName( dataObj.getName() )
            self.setDc( dataObj.getDc() )
            for k in dataObj.keys():
                self[ k ] = dataObj[ k ]
    
    def getSeverity( self ):
        '''
        @return: severity.INFORMATION , all information objects have the same level of severity.
        '''
        return severity.INFORMATION
    
    def setName( self, name ):
        self._name = name
        
    def getName( self ):
        return self._name
    
    def setURL( self, url ):
        self._url = uri2url( url )
    
    def setURI( self, uri ):
        self._uri = uri
        self._url = uri2url( uri )
    
    def setMethod( self, method ):
        self._method = method.upper()
    
    def getMethod( self ):
        return self._method
        
    def setDesc( self, desc ):
        self._desc = desc
        
    def getURL( self ):
        return self._url
    
    def getURI( self ):
        return self._uri
        
    def getDesc( self ):
        if self._id != None and self._id != 0:
            if not self._desc.strip().endswith('.'):
                self._desc += '.'
            
            # One request OR more than one request
            desc_to_return = self._desc
            if len(self._id) > 1:
                desc_to_return += ' This information was found in the requests with'
                desc_to_return += ' ids ' + self._convert_to_range_wrapper( self._id ) + '.'
            else:
                desc_to_return += ' This information was found in the request with'
                desc_to_return += ' id ' + str(self._id[0]) + '.'
                
            return desc_to_return
        else:
            return self._desc
    
    def _convert_to_range_wrapper(self, list_of_integers):
        '''
        Just a wrapper for _convert_to_range; please see documentation below!
        
        @return: The result of self._convert_to_range( list_of_integers ) but without the trailing comma.
        '''
        res = self._convert_to_range( list_of_integers )
        if res.endswith(','):
            res = res[:-1]
        return res
    
    def _convert_to_range(self, list_of_integers):
        '''
        Convert a list of integers to a nicer "range like" string.
        For example:
            input: [1, 2, 3, 4, 5, 6]
            output: '1 to 6'
        
        For example:
            input: [1, 2]
            output: '1 and 2'
            
        For example:
            input: [1, 2, 3, 6]
            output: '1 to 3 and 6'
            
        For example:
            input: [1, 2, 3, 6, 7, 8]
            output: '1 to 3 and 6 to 8'
            
        For example:
            input: [1, 2, 3, 6, 7, 8, 10]
            output: '1 to 3, 6 to 8 and 10'
        '''
        if len(list_of_integers) == 1:
            return str(list_of_integers[0])
        
        elif len(list_of_integers) == 2:
            return str(list_of_integers[0]) + ' and ' + str(list_of_integers[1])
        
        elif len(list_of_integers) > 2:
            # Find the largest sequence like 1, 2, 3, 4...
            start = list_of_integers[0]
            for int_position, int_value in enumerate(list_of_integers[1:]):
                if int_value == start + 1:
                    start = int_value
                else:
                    # This item is the first one from a new sequence
                    break
            
            # Do we have a sequence?
            if int_position != 0:
                # We have a sequence.
                # let's write the string for the current sequence
                response_string = str(list_of_integers[0]) + ' to ' + str(start) + ','
            if int_position == 0:
                response_string = str(list_of_integers[0]) + ','
            
            if int_position + 2 != len(list_of_integers):
                # Now work with the rest of the list:
                response_string += ' ' + self._convert_to_range(list_of_integers[int_position+1:])
            
            # and return...
            return response_string
    
    def __str__( self ):
        return self._desc
        
    def __repr__( self ):
        return '<info object for issue: "'+self._desc+'">'
        
    def setId( self, id ):
        '''
        The id is a unique number that identifies every request and response performed
        by the framework.
        
        The id parameter is usually an integer, that points to that request / response pair.
        
        In some cases, one information object is related to more than one request / response,
        in those cases, the id parameter is a list of integers.
        
        For example, in the cases where the info object is related to one request / response, we get
        this call:
            setId( 3 )
            
        And we save this to the attribute:
            [ 3, ]
            
        When the info object is related to more than one request / response, we get this call:
            setId( [3, 4] )
            
        And we save this to the attribute:
            [ 3, 4]
            
        Also, the list is sorted!
            setId( [4, 3] )
        
        Will save:
            [3, 4]
        '''
        if isinstance(id, type([])):
            # A list with more than one ID:
            
            # I have to check if all of them are actually integers
            for i in id:
                if not isinstance(i, type(5)):
                    # w3afException is correctly handled, I want a crash!
                    raise Exception('All request/response ids have to be integers.')
                    
            id.sort()
            self._id = id
        else:
            self._id = [ id, ]
    
    def getId( self ):
        '''
        @return: The list of ids related to this information object. Please read the
        documentation of setId().
        '''
        return self._id
        
    def setVar( self, variable ):
        self._variable = variable
        
    def getVar( self ):
        return self._variable
        
    def setDc( self, dc ):
        self._dc = dc
        
    def getDc( self ):
        return self._dc
        
    def getToHighlight(self):
        '''
        The string match is the string that was used to identify the vulnerability. For example,
        in a SQL injection the string match would look like:
        
            - "...supplied argument is not a valid MySQL..."
            
        This information is used to highlight the string in the GTK user interface, when showing the
        request / response.
        '''
        return self._string_match
        
    def setToHighlight(self, str_match):
        self._string_match = str_match
