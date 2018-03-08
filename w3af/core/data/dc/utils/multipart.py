"""
multipart.py

Copyright 2014 Andres Riancho

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
import os
import mimetypes

from w3af.core.controllers.misc.io import is_file_like
from w3af.core.data.misc.encoding import smart_str
from w3af.core.data.constants.encodings import DEFAULT_ENCODING


def encode_as_multipart(multipart_container, boundary):
    """
    Encode the DataContainer using multipart/post , given the provided boundary

    :param multipart_container: The container to encode
    :param boundary: Using this boundary (a random string)
    :return: The post-data that should be sent
    """
    v_vars, v_files = _split_vars_files(multipart_container)
    _, data = multipart_encode(v_vars, v_files, boundary=boundary)
    return data


def _split_vars_files(data):
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

        enc_pname = smart_str(pname, encoding=DEFAULT_ENCODING, errors='ignore')

        if is_file_like(value):
            if not value.closed:
                v_files.append((enc_pname, value))
            else:
                v_vars.append((enc_pname, ''))
        elif hasattr(value, 'isFile'):
            v_files.append((enc_pname, value))
        else:
            # Ensuring we actually send a string
            value = smart_str(value, encoding=DEFAULT_ENCODING, errors='ignore')
            v_vars.append((enc_pname, value))

    return v_vars, v_files


def get_boundary():
    """
    Before I used:
        boundary = mimetools.choose_boundary()

    But that returned some "private" information:
        '127.0.0.1.1000.6267.1173556103.828.1'

    Now I simply return a fixed string which I generated once and now re-use
    all the time.

    There is a reason for having a fixed boundary! When comparing two fuzzable
    requests it's easier to do it if the boundaries are static. This allows
    get_request_hash() to work as expected.

    The problem with fixed boundaries is that they might be used to fingerprint
    w3af, or that they might appear in the data we send to the wire and break
    the request.

    :return:
    """
    return 'b08c02-53d780-e2bc43-1d5278-a3c0d9-a5c0d9'


def multipart_encode(_vars, files, boundary=None, _buffer=None):
    if boundary is None:
        boundary = get_boundary()

    if _buffer is None:
        _buffer = ''

    for key, value in _vars:
        _buffer += '--%s\r\n' % boundary
        _buffer += 'Content-Disposition: form-data; name="%s"' % key
        _buffer += '\r\n\r\n' + value + '\r\n'

    for key, fd in files:
        fd.seek(0)
        filename = fd.name.split(os.path.sep)[-1]

        guessed_mime = mimetypes.guess_type(filename)[0]
        content_type = guessed_mime or 'application/octet-stream'
        args = (smart_str(key, errors='ignore'), smart_str(filename, errors='ignore'))

        _buffer += '--%s\r\n' % boundary
        _buffer += 'Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % args
        _buffer += 'Content-Type: %s\r\n' % content_type
        _buffer += '\r\n%s\r\n' % fd.read()

    _buffer += '--%s--\r\n\r\n' % boundary

    return boundary, _buffer
