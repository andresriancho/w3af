"""
auth.py

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
from functools import wraps
from hashlib import sha512

from flask import request

from w3af.core.ui.api import app
from w3af.core.ui.api.utils.error import abort


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return (username == app.config['USERNAME'] and
            sha512(password).hexdigest() == app.config['PASSWORD'])


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        if not 'PASSWORD' in app.config:
            # Auth was not enabled at startup
            return f(*args, **kwargs)

        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            abort(401, 'Could not verify access. Please specify a username and'
                       ' password for HTTP basic authentication.')
        return f(*args, **kwargs)
    
    return decorated
