'''
urlParameterHandler.py

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

import urllib2
import core.data.parsers.urlParser as url_object
from core.data.url.HTTPRequest import HTTPRequest as HTTPRequest


class URLParameterHandler(urllib2.BaseHandler):
    '''
    Appends a user configured URL parameter to the request URL.
    e.g.: http://www.myserver.com/index.html;jsessionid=dd18fa45014ce4fc?id=5
    
    See Section 2.1 URL Syntactic Components of RFC 1808
        <scheme>://<net_loc>/<path>;<params>?<query>#<fragment>
    See Section 3.2.2 of RFC 1738
    
    @author: Kevin Denver ( muffysw@hotmail.com )
    '''
    
    def __init__( self, url_param ):
        self._url_parameter = url_param
        
    def http_request( self, req ):
        url_instance = url_object( req.get_full_url() )
        new_url = url_instance.setParam( self._url_parameter )
        
        new_request = HTTPRequest(new_url, headers=req.headers,
            origin_req_host=req.get_origin_req_host(),
            unverifiable=req.is_unverifiable())
        return new_request

