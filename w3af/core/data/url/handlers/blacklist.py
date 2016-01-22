"""
blacklist.py

Copyright 2013 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
import urllib2
import urllib
import cStringIO
import mimetools

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.config as cf

from w3af.core.data.url.helpers import new_no_content_resp


class BlacklistHandler(urllib2.BaseHandler):
    """
    If the user blacklisted a URL, this handler will know about it and
    return an empty HTTP response.
    
    This feature was in the extended_urllib.py module before, but the problem
    there was that any HTTP responses created and returned at that level did
    not pass through all the other configured handlers and in some cases
    this triggered bugs and errors.
    """

    handler_order = urllib2.HTTPErrorProcessor.handler_order - 1

    def __init__(self):
        non_targets = cf.cf.get('non_targets') or []
        self._non_targets = set()
        self._non_targets.update([url.uri2url() for url in non_targets])

    def default_open(self, req):
        """
        If blacklisted return an empty response, else return None, which means
        that this handler was unable to handle the request and the next one
        needs to be called. With this we want to indicate that the keepalive
        handler will be called.
        """
        if self._is_blacklisted(req.url_object):
            nncr = new_no_content_resp(req.url_object)
            addinfo_inst = http_response_to_httplib(nncr)
            
            return addinfo_inst

        # This means: I don't know how to handle this, call the next opener        
        return None
        
    def _is_blacklisted(self, uri):
        """
        If the user configured w3af to ignore a URL, we are going to be applying
        that configuration here. This is the lowest layer inside w3af.
        """
        if uri.uri2url() in self._non_targets:
            msg = ('The URL you are trying to reach (%s) was configured as a'
                   ' non-target. NOT performing the HTTP request and returning'
                   ' an empty response.')
            om.out.debug(msg % uri)
            return True

        return False


def http_response_to_httplib(nncr):
    header_string = cStringIO.StringIO(str(nncr.get_headers()))
    headers = mimetools.Message(header_string)
    
    addinfo_inst = urllib.addinfourl(cStringIO.StringIO(nncr.get_body()),
                                     headers,
                                     nncr.get_url().url_string,
                                     code=nncr.get_code())
    addinfo_inst.msg = 'No content'
    return addinfo_inst
