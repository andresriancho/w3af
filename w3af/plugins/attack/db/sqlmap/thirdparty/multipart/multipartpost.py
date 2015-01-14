#!/usr/bin/env python

"""
02/2006 Will Holcomb <wholcomb@gmail.com>

Reference: http://odin.himinbi.org/MultipartPostHandler.py

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

import mimetools
import mimetypes
import os
import stat
import StringIO
import sys
import urllib
import urllib2

from lib.core.exception import SqlmapDataException


class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable

# Controls how sequences are uncoded. If true, elements may be given
# multiple values by assigning a sequence.
doseq = 1


class MultipartPostHandler(urllib2.BaseHandler):
    handler_order = urllib2.HTTPHandler.handler_order - 10 # needs to run first

    def http_request(self, request):
        data = request.get_data()

        if data is not None and type(data) != str:
            v_files = []
            v_vars = []

            try:
                for(key, value) in data.items():
                    if isinstance(value, file) or hasattr(value, 'file') or isinstance(value, StringIO.StringIO):
                        v_files.append((key, value))
                    else:
                        v_vars.append((key, value))
            except TypeError:
                systype, value, traceback = sys.exc_info()
                raise SqlmapDataException, "not a valid non-string sequence or mapping object", traceback

            if len(v_files) == 0:
                data = urllib.urlencode(v_vars, doseq)
            else:
                boundary, data = self.multipart_encode(v_vars, v_files)
                contenttype = 'multipart/form-data; boundary=%s' % boundary
                #if (request.has_header('Content-Type') and request.get_header('Content-Type').find('multipart/form-data') != 0):
                #    print "Replacing %s with %s" % (request.get_header('content-type'), 'multipart/form-data')
                request.add_unredirected_header('Content-Type', contenttype)

            request.add_data(data)
        return request

    def multipart_encode(vars, files, boundary = None, buf = None):
        if boundary is None:
            boundary = mimetools.choose_boundary()

        if buf is None:
            buf = ''

        for (key, value) in vars:
            buf += '--%s\r\n' % boundary
            buf += 'Content-Disposition: form-data; name="%s"' % key
            buf += '\r\n\r\n' + value + '\r\n'

        for (key, fd) in files:
            file_size = os.fstat(fd.fileno())[stat.ST_SIZE] if isinstance(fd, file) else fd.len
            filename = fd.name.split('/')[-1] if '/' in fd.name else fd.name.split('\\')[-1]
            try:
                contenttype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            except:
                # Reference: http://bugs.python.org/issue9291
                contenttype = 'application/octet-stream'
            buf += '--%s\r\n' % boundary
            buf += 'Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (key, filename)
            buf += 'Content-Type: %s\r\n' % contenttype
            # buf += 'Content-Length: %s\r\n' % file_size
            fd.seek(0)

            buf = str(buf)
            buf += '\r\n%s\r\n' % fd.read()

        buf += '--%s--\r\n\r\n' % boundary

        return boundary, buf

    multipart_encode = Callable(multipart_encode)

    https_request = http_request
