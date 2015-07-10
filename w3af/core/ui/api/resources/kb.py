"""
kb.py

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
from flask import jsonify, request

import w3af.core.data.kb.knowledge_base as kb

from w3af.core.ui.api import app
from w3af.core.ui.api.utils.error import abort
from w3af.core.ui.api.utils.auth import requires_auth
from w3af.core.ui.api.utils.scans import get_scan_info_from_id


@app.route('/scans/<int:scan_id>/kb/', methods=['GET'])
@requires_auth
def list_kb(scan_id):
    """
    List vulnerabilities stored in the KB (for a specific scan)

    Filters:

        * /scans/0/kb/?name= returns only vulnerabilities which contain the
          specified string in the vulnerability name. (contains)

        * /scans/0/kb/?url= returns only vulnerabilities for a specific URL
          (startswith)

    If more than one filter is specified they are combined using AND.

    :return: A JSON containing a list of:
        - KB resource URL (eg. /scans/0/kb/3)
        - The KB id (eg. 3)
        - The vulnerability name
        - The vulnerability URL
        - Location A
        - Location B
    """
    scan_info = get_scan_info_from_id(scan_id)
    if scan_info is None:
        abort(404, 'Scan not found')

    data = []

    for finding_id, finding in enumerate(kb.kb.get_all_findings()):
        if matches_filter(finding, request):
            data.append(finding_to_json(finding, scan_id, finding_id))

    return jsonify({'items': data})


@app.route('/scans/<int:scan_id>/kb/<int:vulnerability_id>', methods=['GET'])
@requires_auth
def get_kb(scan_id, vulnerability_id):
    """
    The whole information related to the specified vulnerability ID

    :param vulnerability_id: The vulnerability ID to query
    :return: All the vulnerability information
    """
    scan_info = get_scan_info_from_id(scan_id)
    if scan_info is None:
        abort(404, 'Scan not found')

    for finding_id, finding in enumerate(kb.kb.get_all_findings()):
        if vulnerability_id == finding_id:
            return jsonify(finding_to_json(finding, scan_id,
                                           finding_id, detailed=True))

    abort(404, 'Not found')


def matches_filter(finding, request):
    """
    Filters:

        * /scans/0/kb/?name= returns only vulnerabilities which contain the
          specified string in the vulnerability name. (contains)

        * /scans/0/kb/?url= returns only vulnerabilities for a specific URL
          (startswith)

    If more than one filter is specified they are combined using AND.

    :param finding: The vulnerability
    :param request: The HTTP request object
    :return: True if the finding (vulnerability) matches the specified filter
    """
    name = request.args.get('name', None)
    url = request.args.get('url', None)

    if name is not None and url is not None:
        return (name.lower() in finding.get_name().lower() and
                finding.get_url() is not None and
                finding.get_url().url_string.startswith(url))

    elif name is not None:
        return name.lower() in finding.get_name().lower()

    elif url is not None:
        return (finding.get_url() is not None and
                finding.get_url().url_string.startswith(url))

    # No filter
    return True


def finding_to_json(finding, scan_id, finding_id, detailed=False):
    """
    :param finding: The vulnerability
    :param scan_id: The scan ID
    :param finding_id: The vulnerability ID
    :param detailed: Show extra info
    :return: A dict with the finding information
    """
    summary = {'id': finding_id,
               'href': '/scans/%s/kb/%s' % (scan_id, finding_id)}

    if detailed:
        # Get all the data from w3af
        summary.update(finding.to_json())

        # Add the hrefs to the traffic
        traffic_hrefs = []
        for response_id in summary['response_ids']:
            args = (scan_id, response_id)
            traffic_href = '/scans/%s/traffic/%s' % args
            traffic_hrefs.append(traffic_href)

        summary['traffic_hrefs'] = traffic_hrefs
    else:
        # Support findings without a URL
        url = finding.get_url().url_string if finding.get_url() else None

        summary.update({'name': finding.get_name(),
                        'url': url})

    return summary
