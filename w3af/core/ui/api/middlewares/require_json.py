"""
require_json.py

Copyright 2016 Andres Riancho

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
from flask import request

from w3af.core.ui.api import app
from w3af.core.ui.api.utils.error import abort

NO_HEADER = 'HTTP request header Content-Type must be application/json'
INVALID_JSON = 'HTTP request body must be valid JSON object.'


@app.before_request
def require_json():
    """
    Helper to let users know that they should submit the content-type header
    https://github.com/andresriancho/w3af/issues/13323

    :return: abort() if an error occured
    """
    if request.method in {'GET', 'HEAD', 'DELETE'}:
        return

    if request.mimetype != 'application/json':
        abort(400, NO_HEADER)

    json_data = request.get_json(silent=True)
    if json_data is None:
        abort(400, INVALID_JSON)
