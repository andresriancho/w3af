"""
version.py

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

from w3af.core.ui.api import app
from w3af.core.ui.api.utils.auth import requires_auth
from w3af.core.controllers.misc.get_w3af_version import get_w3af_version_as_dict


@app.route('/version', methods=['GET'])
@requires_auth
def version():
    return jsonify(get_w3af_version_as_dict())
