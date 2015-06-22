"""
security_headers.py

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
from w3af.core.ui.api import app


@app.after_request
def add_security_headers(response):
    response.headers['Server'] = 'REST API - w3af'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Expires'] = '0'

    if 'application/json' in response.content_type:
        # Add the charset
        response.content_type = 'application/json; charset=UTF-8'

    return response