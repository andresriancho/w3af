"""
fuzzable_requests.py

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
from base64 import b64encode

import w3af.core.data.kb.knowledge_base as kb

from w3af.core.ui.api import app
from w3af.core.ui.api.utils.error import abort
from w3af.core.ui.api.utils.auth import requires_auth
from w3af.core.ui.api.utils.scans import get_scan_info_from_id


@app.route('/scans/<int:scan_id>/fuzzable-requests/', methods=['GET'])
@requires_auth
def get_fuzzable_request_list(scan_id):
    """
    A list with all the known fuzzable requests by this scanner

    :param scan_id: The scan ID
    :return: Fuzzable requests (serialized as base64 encoded string) in a list
    """
    scan_info = get_scan_info_from_id(scan_id)
    if scan_info is None:
        abort(404, 'Scan not found')

    data = []

    for fuzzable_request in kb.kb.get_all_known_fuzzable_requests():
        data.append(b64encode(fuzzable_request.dump()))

    return jsonify({'items': data})
