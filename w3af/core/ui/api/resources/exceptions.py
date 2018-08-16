"""
exceptions.py

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
import sys

from flask import jsonify

from w3af.core.ui.api import app
from w3af.core.ui.api.utils.error import abort
from w3af.core.ui.api.utils.auth import requires_auth
from w3af.core.ui.api.utils.scans import get_scan_info_from_id
from w3af.core.controllers.core_helpers.status import CoreStatus


@app.route('/scans/<int:scan_id>/exceptions/', methods=['GET'])
@requires_auth
def list_exceptions(scan_id):
    """
    List all exceptions found during a scan

    :return: A JSON containing a list of:
        - Exception resource URL (eg. /scans/0/exceptions/3)
        - The exceptions id (eg. 3)
        - Exception string
        - Exception file name
        - Exception line number
    """
    scan_info = get_scan_info_from_id(scan_id)
    if scan_info is None:
        abort(404, 'Scan not found')

    data = []

    all_exceptions = scan_info.w3af_core.exception_handler.get_all_exceptions()

    for exception_id, exception_data in enumerate(all_exceptions):
        data.append(exception_to_json(exception_data, scan_id, exception_id))

    return jsonify({'items': data})


@app.route('/scans/<int:scan_id>/exceptions/<int:exception_id>',
           methods=['GET'])
@requires_auth
def get_exception_details(scan_id, exception_id):
    """
    The whole information related to the specified exception ID

    :param exception_id: The exception ID to query
    :return: All the vulnerability information
    """
    scan_info = get_scan_info_from_id(scan_id)
    if scan_info is None:
        abort(404, 'Scan not found')

    all_exceptions = scan_info.w3af_core.exception_handler.get_all_exceptions()

    for i_exception_id, exception_data in enumerate(all_exceptions):
        if exception_id == i_exception_id:
            return jsonify(exception_to_json(exception_data, scan_id,
                                             exception_id, detailed=True))

    abort(404, 'Not found')


def exception_to_json(exception_data, scan_id, exception_id, detailed=False):
    """
    :param exception_data: The ExceptionData instance
    :param scan_id: The scan ID
    :param exception_id: The exception ID in the REST API
    :param detailed: Show extra info
    :return: A dict with the exception information
    """
    summary = {'id': exception_id,
               'href': '/scans/%s/exceptions/%s' % (scan_id, exception_id)}

    # Get all the data from w3af
    summary.update(exception_data.to_json())

    if not detailed:
        summary.pop('traceback')

    return summary


@app.route('/scans/<int:scan_id>/exceptions/', methods=['POST'])
@requires_auth
def exception_creator(scan_id):
    """
    Mostly for testing, but have fun playing ;)

    :return: None, just create a new exception in the exception handler for this
             scan, helps me with the unittest process.
    """
    scan_info = get_scan_info_from_id(scan_id)
    if scan_info is None:
        abort(404, 'Scan not found')

    current_status = FakeStatus(None)
    current_status.set_running_plugin('phase', 'plugin')
    current_status.set_current_fuzzable_request('phase',
                                                'http://www.w3af.org/')

    try:
        raise Exception('unittest')
    except Exception, exception:
        exec_info = sys.exc_info()
        enabled_plugins = ''

        scan_info.w3af_core.exception_handler.write_crash_file = lambda x: x
        scan_info.w3af_core.exception_handler.handle(current_status, exception,
                                                     exec_info, enabled_plugins)

    return jsonify({'code': 201}), 201


class FakeStatus(CoreStatus):
    pass