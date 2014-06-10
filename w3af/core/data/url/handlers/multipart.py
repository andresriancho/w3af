####
# 02/2006 Will Holcomb <wholcomb@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
import urllib2
import mimetools
import mimetypes
import os
import hashlib

from w3af.core.controllers.misc.io import is_file_like
from w3af.core.data.misc.encoding import smart_str
from w3af.core.data.constants.encodings import DEFAULT_ENCODING

# Controls how sequences are uncoded. If true, elements may be given multiple
# values by assigning a sequence.
doseq = 1


class MultipartPostHandler(urllib2.BaseHandler):
    """
    Enables the use of multipart/form-data for posting forms using urllib2

    Inspirations:
      Upload files in python:
        http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/146306
      urllib2_file:
        Fabien Seisen: <fabien@seisen.org>

    Example:
      import MultipartPostHandler, urllib2, cookielib

      cookies = cookielib.CookieJar()
      opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),
                                    MultipartPostHandler.MultipartPostHandler)
      params = { "username" : "bob", "password" : "riviera",
                 "file" : open("filename", "rb") }
      opener.open("http://wwww.bobsite.com/upload/", params)

    Further Example:
      The main function of this file is a sample which downloads a page and
      then uploads it to the W3C validator.
    """
    # needs to run first
    handler_order = urllib2.HTTPHandler.handler_order - 10

    def http_request(self, request):
        data = request.get_raw_data()

        if self._should_send_as_multipart(request):

            v_vars, v_files = self._split_vars_files(data)

            boundary, data = multipart_encode(v_vars, v_files)

            # Note that this replaces any old content-type
            contenttype = 'multipart/form-data; boundary=%s' % boundary
            request.add_unredirected_header('Content-Type', contenttype)

            request.add_data(data)

        return request

    # I also want this to work with HTTPS!
    https_request = http_request

    def _should_send_as_multipart(self, request):
        content_type, _ = request.get_headers().iget('content-type', '')
        has_multipart_header = 'multipart' in content_type

        return self._has_files(request.get_raw_data()) or has_multipart_header

    def _has_files(self, post_data):
        """
        :return: True if the data_container passed as parameter contains files
        """
        for token in post_data.iter_tokens():

            value = token.get_value()

            if isinstance(value, basestring):
                continue

            elif is_file_like(value):
                return True

        return False

    def _split_vars_files(self, data):
        """
        Based on the request it decides if we should send the request as
        multipart or not.

        :return: (List with string variables,
                  List with file variables)
        """
        v_vars = []
        v_files = []

        for token in data.iter_tokens():

            pname = token.get_name()
            value = token.get_value()

            enc_pname = smart_str(pname, encoding=DEFAULT_ENCODING)

            if is_file_like(value):
                if not value.closed:
                    v_files.append((enc_pname, value))
                else:
                    v_vars.append((enc_pname, ''))
            elif hasattr(value, 'isFile'):
                v_files.append((enc_pname, value))
            else:
                # Ensuring we actually send a string
                value = smart_str(value, encoding=DEFAULT_ENCODING)
                v_vars.append((enc_pname, value))

        return v_vars, v_files


def multipart_encode(_vars, files, boundary=None, _buffer=None):
    if boundary is None:
        # Before:
        #     boundary = mimetools.choose_boundary()
        #     '127.0.0.1.1000.6267.1173556103.828.1'
        # This contains my IP address, I dont like that...
        # Now:
        m = hashlib.md5()
        m.update(mimetools.choose_boundary())
        boundary = m.hexdigest()

    if _buffer is None:
        _buffer = ''

    for key, value in _vars:
        _buffer += '--%s\r\n' % boundary
        _buffer += 'Content-Disposition: form-data; name="%s"' % key
        _buffer += '\r\n\r\n' + value + '\r\n'

    for key, fd in files:
        fd.seek(0)
        filename = fd.name.split(os.path.sep)[-1]
        contenttype = mimetypes.guess_type(
            filename)[0] or 'application/octet-stream'
        _buffer += '--%s\r\n' % boundary
        _buffer += 'Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (key, filename)
        _buffer += 'Content-Type: %s\r\n' % contenttype
        _buffer += '\r\n' + fd.read() + '\r\n'

    _buffer += '--%s--\r\n\r\n' % boundary

    return boundary, _buffer
