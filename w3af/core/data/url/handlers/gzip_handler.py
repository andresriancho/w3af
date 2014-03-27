"""
gzip_handler.py

Copyright 2006 Andres Riancho

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
import gzip

from cStringIO import StringIO

from w3af.core.data.url.handlers.cache import SQLCachedResponse


class HTTPGzipProcessor(urllib2.BaseHandler):
    handler_order = 200  # response processing before HTTPEquivProcessor

    def http_request(self, request):
        request.add_header("Accept-encoding", "gzip")
        return request

    def http_response(self, request, response):
        """
        Decompress the HTTP response and send it to the next handler.
        """
        # First I need to check if the response came from the cache
        # stuff that's stored in the cache is there uncompressed,
        # so I can simply return the same response!
        if isinstance(response, SQLCachedResponse):
            return response

        #
        # post-process response
        #
        enc_hdrs = response.info().getheaders("Content-encoding")
        for enc_hdr in enc_hdrs:
            if ("gzip" in enc_hdr) or ("compress" in enc_hdr):
                # Decompress
                try:
                    data = gzip.GzipFile(
                        fileobj=StringIO(response.read())).read()
                except:
                    # I get here when the HTTP response body is corrupt
                    # return the same thing that I got... can't do magic yet!
                    return response
                else:
                    # The response was successfully unzipped
                    response.set_body(data)
                    return response
        return response

    https_request = http_request
    https_response = http_response
