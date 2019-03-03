"""
state.py

Copyright 2019 Kartik Verma

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
from w3af.core.ui.api.utils.auth import requires_auth
from w3af.core.ui.api.utils.scans import get_scan_info_from_id
from w3af.core.ui.api.resources.kb import finding_to_json
from w3af.core.ui.api.utils.error import abort
import w3af.core.data.kb.knowledge_base as kb

from flask import jsonify


@app.route('/scans/<int:scan_id>/state/', methods=['GET'])
@requires_auth
def get_current_state(scan_id):
    scan_info = get_scan_info_from_id(scan_id)
    if scan_info is None:
        abort(404, 'Scan not found')
    kb_list = []
    result = {}
    result['id'] = scan_id
    for finding_id, finding in enumerate(kb.kb.get_all_findings()):
        finding = finding_to_json(finding, scan_id, finding_id, detailed=True)
        kb_list.append(finding)
    result['kb'] = kb_list
    scan_info = get_scan_info_from_id(scan_id)
    if scan_info is None:
        abort(404, 'Scan not found')
    exc = scan_info.exception
    status = scan_info.w3af_core.status.get_status_as_dict()
    status['exception'] = exc if exc is None else str(exc)
    result['status'] = status
    return jsonify(result)

    
