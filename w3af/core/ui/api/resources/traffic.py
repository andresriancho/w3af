"""
traffic.py

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
from base64 import b64encode
from flask import jsonify

from w3af.core.ui.api import app
from w3af.core.ui.api.utils.error import abort
from w3af.core.ui.api.utils.auth import requires_auth
from w3af.core.ui.api.utils.scans import get_scan_info_from_id
from w3af.core.data.db.history import HistoryItem
from w3af.core.controllers.exceptions import DBException


@app.route('/scans/<int:scan_id>/traffic/<int:traffic_id>', methods=['GET'])
@requires_auth
def get_traffic_details(scan_id, traffic_id):
    """
    The HTTP request and response associated with a vulnerability, usually the
    user will first get /scans/1/kb/3 and from there (if needed) browse to
    this resource where the HTTP traffic is available

    :param scan_id: The scan ID
    :param traffic_id: The ID of the request/response
    :return: HTTP request and response in base64 format
    """
    scan_info = get_scan_info_from_id(scan_id)
    if scan_info is None:
        abort(404, 'Scan not found')

    history_db = HistoryItem()

    try:
        details = history_db.read(traffic_id)
    except DBException:
        msg = 'Failed to retrieve request with id %s from DB.'
        abort(404, msg)
        return

    data = {'request': b64encode(details.request.dump()),
            'response': b64encode(details.response.dump())}

    return jsonify(data)
