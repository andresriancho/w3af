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


@app.route('/kb/', methods=['GET'])
def list_kb():
    """
    List vulnerabilities stored in the KB

    Filters:

        * /kb/?name= returns only vulnerabilities which contain the specified
          string in the vulnerability name. (contains)

        * /kb/?url= returns only vulnerabilities for a specific URL (startswith)

    If more than one filter is specified they are combined using AND.

    :return: A JSON containing a list of:
        - KB resource URL (eg. /kb/3)
        - The KB id (eg. 3)
        - The vulnerability name
        - The vulnerability URL
        - Location A
        - Location B
    """
    data = []

    for finding_id, finding in enumerate(kb.kb.get_all_findings()):
        if matches_filter(finding, request):
            data.append(finding_to_json(finding, finding_id))

    return jsonify(data)


@app.route('/kb/<int:vulnerability_id>', methods=['GET'])
def get_kb(vulnerability_id):
    """
    The whole information related to the specified vulnerability ID

    :param vulnerability_id: The vulnerability ID to query
    :return: All the vulnerability information
    """
    for finding_id, finding in enumerate(kb.kb.get_all_findings()):
        if vulnerability_id == finding_id:
            return jsonify(finding_to_json(finding, finding_id, detailed=True))

    abort(404, 'Not found')


def matches_filter(finding, request):
    """
    Filters:

        * /kb/?name= returns only vulnerabilities which contain the specified
          string in the vulnerability name. (contains)

        * /kb/?url= returns only vulnerabilities for a specific URL (startswith)

    If more than one filter is specified they are combined using AND.

    :param finding: The vulnerability
    :param request: The HTTP request object
    :return: True if the finding (vulnerability) matches the specified filter
    """
    name = request.args.get('name', None)
    url = request.args.get('url', None)

    if name is not None and url is not None:
        return name in finding.get_name() and finding.get_url().startswith(url)

    elif name is not None:
        return name in finding.get_name()

    elif url is not None:
        return finding.get_url().url_string.startswith(url)

    # No filter
    return True


def finding_to_json(finding, finding_id, detailed=False):
    """
    :param finding: The vulnerability
    :param finding_id: The vulnerability ID
    :param detailed: Show extra info
    :return: A dict with the finding information
    """
    summary = {'id': finding_id,
               'href': '/kb/%s' % finding_id}

    if detailed:
        summary.update(finding.to_json())
    else:
        summary.update({'name': finding.get_name(),
                        'url': finding.get_url()})

    return summary