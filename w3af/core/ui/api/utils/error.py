"""
error.py

Copyright 2015 Andres Riancho

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
import json
from werkzeug.exceptions import HTTPException


class JSONHTTPException(HTTPException):
    def __init__(self, description=None, code=None):
        Exception.__init__(self)
        self.response = None
        self.description = description
        self.code = code

    def get_body(self, environ=None):
        """Get the JSON body"""
        return json.dumps({'message': self.description,
                           'code': self.code})

    def get_headers(self, environ=None):
        """Get a list of headers."""
        return [('Content-Type', 'application/json')]


def abort(code, message):
    """
    Raise an exception to stop HTTP processing execution

    :param code: 403, 500, etc.
    :param message: A message to show to the user
    :return: None, an exception is raised
    """
    raise JSONHTTPException(message, code)
