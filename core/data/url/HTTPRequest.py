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


class HTTPRequest(urllib2.Request):
    
    def __init__(self, url, data=None, headers={},
                 origin_req_host=None, unverifiable=False):
        
        # Call the base class
        urllib2.Request.__init__(self, url, data, headers, origin_req_host, unverifiable)

        
