'''
fuzzableRequest.py

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

from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
from core.data.dc.dataContainer import dataContainer as dc
from core.data.dc.cookie import cookie as cookie
import core.data.kb.config as cf
from core.data.parsers.urlParser import *
import copy
import urllib

#CR = '\r'
CR = ''
LF = '\n'
CRLF = CR + LF
SP = ' '

class fuzzableRequest(object):
    '''
    This class represents a fuzzable request. Fuzzable requests where created to allow w3af plugins
    to be much simpler and dont really care if the vulnerability is in the postdata, querystring, header, cookie
    or some other variable.
    
    Other classes should inherit from this one and change the behaviour of getURL() and getData(). For
    example: the class httpQsRequest should return the _dc in the querystring ( getURL ) and httpPostDataRequest
    should return the _dc in the POSTDATA ( getData() ).
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        
        # Internal variables
        self._url = ''
        self._method = 'GET'
        self._uri = ''
        self._data = ''
        self._headers = {}
        self._cookie = None
        self._dc = dc()

        # Set the internal variables
        self._sent_information = None
    
    def dump( self ):
        '''
        @return: a DETAILED str representation of this fuzzable request.
        '''
        result_string = ''
        result_string += self.dumpRequestHead()
        result_string += CRLF
        if self.getData():
            result_string += str( self.getData() )
        return result_string
    
    def getRequestLine(self):
        '''Return request line.'''
        return self.getMethod() + SP + self.getURI() + SP + 'HTTP/1.1' + CRLF

    def dumpRequestHead( self ):
        '''
        @return: A string with the head of the request
        '''
        res = ''
        res += self.getRequestLine()
        res += self.dumpHeaders()
        return res
    
    def dumpHeaders( self ):
        '''
        @return: a str representation of the headers.
        '''
        result_string = ''
        for header in self._headers:
            result_string += header + ': ' + self._headers[ header ] + CRLF
        return result_string

    def export( self ):
        '''
        METHOD,URL,DC
        Examples:
        GET,http://localhost/index.php?abc=123&def=789,
        POST,http://localhost/index.php,abc=123&def=789
        
        @return: a csv str representation of the request
        '''
        #
        #   FIXME: What if a comma is inside the URL or DC?
        #   TODO: Why don't we export headers and cookies?
        #
        str_res = ''
        str_res += self._method + ',' 
        str_res += self._url

        if self._method == 'GET': 
            if self._dc:
                str_res += '?'
                str_res += str(self._dc)         
            str_res += ','
        else:
            str_res += ','
            if self._dc:
                str_res += str(self._dc)
        return str_res
                    
    def sent(self, something_interesting):
        '''
        Checks if the something_interesting was sent in the request.

        @parameter something_interesting: The string
        @return: True if it was sent
        '''
        if self._sent_information is None:
            self._sent_information = ''
    
            if self.getMethod().upper() == 'POST':
                sent_data = self.getData()
                
                if sent_data is not None:
                    
                    # Save the information as-is, encoded.
                    self._sent_information += ' ' + str(sent_data)
                    
                    # Save the decoded information
                    sent_data = urllib.unquote( str(sent_data) )
                    self._sent_information += ' ' + sent_data
                    
            
            # Save the url as-is, encoded.
            self._sent_information += ' ' + self.getURI()
            # Save the decoded URL
            self._sent_information += ' ' + urllib.unquote_plus( self.getURI() )
    
        if something_interesting in self._sent_information:
            return True
        else:
            # I didn't sent the something_interesting in any way
            return False

    def __str__( self ):
        '''
        Return a str representation of this fuzzable request.
        '''
        result_string = ''
        result_string += self._url
        result_string += ' | Method: ' + self._method
        
        if self._dc:
            result_string += ' | Parameters: ('
            
            # Mangle the value for printing
            for param_name in self._dc:

                #
                # Because of repeated parameter names, we need to add this:
                #
                for the_value in self._dc[param_name]:

                    # the_value is always a string
                    if len(the_value) > 10:
                        the_value = the_value[:10] + '...'
                    the_value = '"' + the_value + '"'
                    
                    result_string += param_name + '=' + the_value + ', '
                    
            result_string = result_string[: -2]
            result_string += ')'
        return result_string
        
    def __eq__( self, other ):
        '''
        Two requests are equal if:
            - They have the same URL
            - They have the same method
            - They have the same parameters
            - The values for each parameter is equal
        
        @return: True if the requests are equal.
        '''
        if self._uri == other._uri and\
        self._method == other._method and\
        self._dc == other._dc:
            return True
        else:
            return False
            
    def is_variant_of(self, other):
        '''
        Two requests are loosely equal (or variants) if:
            - They have the same URL
            - They have the same HTTP method
            - They have the same parameter names
            - The values for each parameter have the same type (int / string)
            
        @return: True if self and other are variants.
        '''
        if self._uri == other._uri and\
        self._method == other._method and\
        self._dc.keys() == other._dc.keys():
                
            #
            #   Ok, so it has the same URI, method, dc:
            #   I need to work now :(
            #
            
            #   What I do now, is check if the values for each parameter has the same
            #   type or not.
            for param_name in self._dc:
                
                #   repeated parameter names
                for index in xrange(len(self._dc[param_name])):
                    try:
                        #   I do it in a try, because "other" might not have that many repeated
                        #   parameters, and index could be out of bounds.
                        value_self = self._dc[param_name][index]
                        value_other = other._dc[param_name][index]
                    except IndexError, e:
                        return False
                    else:
                        if value_other.isdigit() and not value_self.isdigit():
                            return False
                        elif value_self.isdigit() and not value_other.isdigit():
                            return False

            return True
        else:
            return False
        
    
    def __ne__( self,other):
        return not self.__eq__( other )
    
    def setURL( self , url ):
        self._url = url.replace(' ', '%20')
        self._uri = self._url
    
    def setURI( self, uri ):
        self._uri = uri.replace(' ', '%20')
        self._url = uri2url( uri )
        
    def setMethod( self , method ):
        self._method = method
        
    def setDc( self , dataCont ):
        if isinstance(dataCont, dc):
            self._dc = dataCont
        else:
            msg = 'Invalid call to fuzzableRequest.setDc(), the argument must be a'
            msg += ' dataContainer instance.'
            raise w3afException( msg )
        
    def setHeaders( self , headers ):
        self._headers = headers
    
    def setReferer( self, referer ):
        self._headers[ 'Referer' ] = referer
    
    def setCookie( self , c ):
        '''
        @parameter cookie: A cookie object as defined in core.data.dc.cookie, or a string.
        '''
        if isinstance( c, cookie):
            self._cookie = c
        elif isinstance( c, basestring ):
            self._cookie = cookie( c )
        elif c is None:
            self._cookie = None
        else:
            om.out.error('[fuzzableRequest error] setCookie received: "' + str(type(c)) + '" , "' + repr(c) + '"'  )
            raise w3afException('Invalid call to fuzzableRequest.setCookie()')
            
    def getURL( self ):
        return self._url
    
    def getURI( self ):
        return self._uri
        
    def setData( self, d ):
        '''
        The data is the string representation of the dataContainer, in most cases it wont be set.
        '''
        self._data = d
        
    def getData( self ):
        '''
        The data is the string representation of the dataContainer, in most cases it will be used as the POSTDATA for requests.
        Sometimes it is also used as the query string data.
        '''
        return self._data
        
    def getMethod( self ):
        return self._method
        
    def getDc( self ):
        return self._dc
        
    def getHeaders( self ):
        return self._headers
    
    def getReferer( self ):
        if 'Referer' in self._headers['headers']:
            return self._headers['Referer']
        else:
            return ''
    
    def getCookie( self ):
        if self._cookie:
            return self._cookie
        else:
            return None
    
    def getFileVariables( self ):
        return []
    
    def copy( self ):
        newFr = copy.deepcopy( self )
        return newFr

    def __repr__( self ):
        return '<fuzzable request | '+ self.getMethod() +' | '+ self.getURI() +' >'
