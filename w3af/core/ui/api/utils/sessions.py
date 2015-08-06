"""
sessions.py

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
from flask import jsonify

from functools import wraps

from w3af.core.ui.api.db.master import SCANS


def check_session_exists(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        scan_id = kwargs['scan_id']
        if scan_id not in SCANS:
            return jsonify({
                'code': 404,
                'message': 'Session with ID %s does not exist' % scan_id
            }), 404
        return f(*args, **kwargs)
    return decorated
