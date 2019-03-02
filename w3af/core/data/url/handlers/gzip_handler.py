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
import zlib

from cStringIO import StringIO

from w3af.core.data.url.handlers.cache import SQLCachedResponse


class HTTPGzipProcessor(urllib2.BaseHandler):

    # response processing before HTTPEquivProcessor
    handler_order = 200

    def __init__(self):
        self._decompression_methods = [
            self._gzip_0,
            self._zlib_0,
            self._zlib_1
        ]

    def http_request(self, request):
        request.add_header('Accept-encoding', 'gzip, deflate')
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
        if self._should_decompress(response):
            response = self._decompress(response)

        return response

    def _gzip_0(self, body):
        return gzip.GzipFile(fileobj=StringIO(body)).read()

    def _zlib_0(self, body):
        # RFC 1950
        return zlib.decompress(body)

    def _zlib_1(self, body):
        # RFC 1951
        return zlib.decompress(body, -zlib.MAX_WBITS)

    def _decompress(self, response):
        """
        :param response: HTTP response
        :return: HTTP response with decompressed body
        """
        body = response.read()

        decompressed_body = None
        decompression_method = None

        for decompression_method in self._decompression_methods:
            try:
                decompressed_body = decompression_method(body)
            except:
                continue
            else:
                break

        if decompressed_body is not None:
            # The response was successfully decompressed
            response.set_body(decompressed_body)

            # The decompression method that worked should be moved to the
            # beginning of the list (if not there yet)
            if self._decompression_methods.index(decompression_method) != 0:
            
                dm_temp = self._decompression_methods[:]
                dm_temp.remove(decompression_method)
                dm_temp.insert(0, decompression_method)

                self._decompression_methods = dm_temp

        return response

    def _should_decompress(self, response):
        """
        :param response: The HTTP response
        :return: True if the HTTP response contains headers that indicate the
                 content is compressed and this handler should decompress it
        """
        for enc_hdr in response.info().getheaders('Content-encoding'):
            if 'gzip' in enc_hdr:
                return True

            if 'compress' in enc_hdr:
                return True

            if 'deflate' in enc_hdr:
                return True

        return False

    https_request = http_request
    https_response = http_response
