'''
HTTPRequest.py

Copyright 2010 Andres Riancho

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

import urllib2
import urllib
import copy

from core.data.parsers.urlParser import url_object


class HTTPRequest(urllib2.Request):
    
    def __init__(self, url, data=None, headers={},
                 origin_req_host=None, unverifiable=False):
        '''
        This is a simple wrapper around a urllib2 request object.
        
        >>> r = HTTPRequest('http://www.google.com')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: The url __init__ parameter of a HTTPRequest object must be of urlParser.url_object type.
        
        >>> u = url_object('http://www.google.com')
        >>> r = HTTPRequest(u)
        '''
        if not isinstance(url, url_object):
            raise ValueError('The url __init__ parameter of a HTTPRequest object must be of urlParser.url_object type.')
        
        #
        #    Save some information for later access in an easier way
        #
        self.url_object = url
        
        # Call the base class
        urllib2.Request.__init__(self, url.url_string, data, headers, origin_req_host, unverifiable)

    def copy(self):
        return copy.deepcopy( self )
